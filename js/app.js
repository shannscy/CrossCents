/* CrossCents — shared app logic
   -----------------------------------------------------------------------
   The login pages (freelancer-login.html / company-login.html) are wired
   to the crosscents Descope project. Descope proves WHO signed in; the
   FastAPI backend (backend/) is the only thing that decides WHAT they're
   allowed to do — it independently validates the Descope session and
   resolves the user's role/organisation itself. The browser never gets to
   assert "I'm a company admin" and have that trusted.
   ----------------------------------------------------------------------- */

const DESCOPE_PROJECT_ID = "P3HZlcn7sECUmwT4OWWOSR72I2fa";
const FREELANCER_FLOW_ID = "freelancer-sign-up-or-in";       // magic link + social, no MFA
const COMPANY_FLOW_ID = "company-admin-sign-up-or-in";       // magic link/social, verified email only + mandatory TOTP MFA
const BANK_LINK_STEP_UP_FLOW_ID = "freelancer-link-bank-step-up";
const WITHDRAW_STEP_UP_FLOW_ID = "freelancer-withdraw-step-up"; // OTP step-up before withdrawal

// Points at the deployed Render backend so the live GitHub Pages site works.
// Change to "http://localhost:8000" if you're running the backend locally
// instead (and serving this frontend locally too — see backend/README.md).
const API_BASE_URL = "https://crosscents-backend.onrender.com";

/* --------------------------- session token ------------------------------
   sessionStorage here holds only a bearer token (and a display-only name
   for greeting text) — never a role. It's a credential to send to the
   backend, not something the frontend trusts on its own. Every real
   authorization decision is re-derived by FastAPI on every request via
   Session.requireRole() below, which calls the backend, not this storage.
   ------------------------------------------------------------------------- */

const SessionToken = {
  KEY: "crosscents_session_token",
  NAME_KEY: "crosscents_display_name",
  set(token, displayName) {
    sessionStorage.setItem(SessionToken.KEY, token);
    if (displayName) sessionStorage.setItem(SessionToken.NAME_KEY, displayName);
  },
  get() {
    return sessionStorage.getItem(SessionToken.KEY);
  },
  getDisplayName() {
    return sessionStorage.getItem(SessionToken.NAME_KEY) || "";
  },
  clear() {
    sessionStorage.removeItem(SessionToken.KEY);
    sessionStorage.removeItem(SessionToken.NAME_KEY);
  },
};

function logout(redirectTo) {
  SessionToken.clear();
  window.location.href = redirectTo || "index.html";
}

/* ------------------------------- API client ------------------------------
   Every call attaches the Descope session JWT as a Bearer token. The
   backend independently validates it and decides the response — a 401/403
   here means the backend rejected it, not that the frontend decided anything.
   ------------------------------------------------------------------------- */

class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `Request failed (${status})`);
    this.status = status;
  }
}

async function api(path, { method = "GET", body } = {}) {
  const token = SessionToken.get();
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = "Bearer " + token;

  const res = await fetch(API_BASE_URL + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    // no/invalid JSON body — fine for some error responses
  }

  if (!res.ok) {
    throw new ApiError(res.status, data && data.detail);
  }
  return data;
}

/* --------------------------------- Session -------------------------------
   requireRole() is what every dashboard page calls on load. It asks the
   BACKEND who the caller is and what role they actually have — it does not
   trust anything cached in the browser. If the backend says "not
   authenticated" or "wrong role," we redirect to sign-in, full stop.
   ------------------------------------------------------------------------- */

const Session = {
  // Non-redirecting check, for pages that work fine for signed-out visitors
  // (e.g. the public job board) but personalize themselves when a real
  // session is present. Never trust the result for gating an action —
  // use requireRole() for that.
  async currentOrNull() {
    if (!SessionToken.get()) return null;
    try {
      return await api("/me");
    } catch (err) {
      console.error("Session.currentOrNull(): /me failed —", err.status, err.message);
      return null;
    }
  },

  async requireRole(role, redirectTo) {
    if (!SessionToken.get()) {
      console.warn("Session.requireRole(): no token in sessionStorage, redirecting to", redirectTo);
      window.location.href = redirectTo;
      return null;
    }
    try {
      const me = await api("/me");
      if (me.role !== role) {
        console.warn(`Session.requireRole(): backend says role="${me.role}", page wants "${role}" — redirecting`);
        window.location.href = redirectTo;
        return null;
      }
      return me;
    } catch (err) {
      console.error("Session.requireRole(): /me failed —", err.status, err.message, "— redirecting to", redirectTo);
      window.location.href = redirectTo;
      return null;
    }
  },
};

function formatCurrency(n, currency = "USD") {
  const amount = Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return currency === "USD" ? "$" + amount : currency + " " + amount;
}

function formatDate(isoString) {
  try {
    return new Date(isoString).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } catch (_) {
    return isoString;
  }
}

function formatDateTime(isoString) {
  try {
    return new Date(isoString).toLocaleString("en-US", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch (_) {
    return isoString;
  }
}

/* ---------------------------- job marketplace ---------------------------- */
/* Unchanged — this part of the app is still pure sample data, no backend
   behind it yet, and out of scope for the auth/ledger hardening pass. */

const JOB_CATEGORIES = ["Sales", "Tech", "Business Development", "Marketing", "Design", "Operations"];

const SAMPLE_JOBS = [
  { id: "j1", title: "Account Executive", company: "Growthly Labs", category: "Sales", type: "Short-term", duration: "3 months", budget: "$9,000/mo", location: "Remote", posted: "Aug 5, 2026", description: "Own the full sales cycle for our mid-market SaaS product, from discovery to close.", skills: ["B2B SaaS", "CRM", "Outbound Sales"] },
  { id: "j2", title: "Sales Development Rep", company: "Solace Analytics", category: "Sales", type: "Short-term", duration: "6 months", budget: "$5,000/mo", location: "Remote", posted: "Aug 3, 2026", description: "Qualify inbound leads and build outbound pipeline for our analytics platform.", skills: ["Cold Outreach", "HubSpot", "Qualifying"] },
  { id: "j3", title: "Frontend Engineer (React)", company: "Fenwick & Co", category: "Tech", type: "One-off", duration: "6-week build", budget: "$12,000 flat", location: "Remote", posted: "Aug 6, 2026", description: "Ship a new customer-facing dashboard in React and TypeScript.", skills: ["React", "TypeScript", "CSS"] },
  { id: "j4", title: "Backend Engineer (Node.js)", company: "Xentir Pte Ltd", category: "Tech", type: "Short-term", duration: "4 months", budget: "$95/hr", location: "Remote", posted: "Jul 30, 2026", description: "Build out our payments service's ledger API on Node.js and Postgres.", skills: ["Node.js", "PostgreSQL", "AWS"] },
  { id: "j5", title: "Business Development Manager", company: "Northwind Labs", category: "Business Development", type: "Short-term", duration: "6 months", budget: "$7,500/mo", location: "Remote (US hours)", posted: "Aug 1, 2026", description: "Source and close regional partnerships to open a new market.", skills: ["Partnerships", "Lead Gen", "Negotiation"] },
  { id: "j6", title: "Product Marketing Manager", company: "Solace Analytics", category: "Marketing", type: "Short-term", duration: "3 months", budget: "$6,800/mo", location: "Remote", posted: "Jul 28, 2026", description: "Lead positioning and launch for our new analytics module.", skills: ["Positioning", "Content", "Launch"] },
  { id: "j7", title: "Growth Marketer", company: "Vantage Cloud", category: "Marketing", type: "One-off", duration: "Campaign", budget: "$4,200 flat", location: "Remote", posted: "Aug 4, 2026", description: "Run a paid social and SEO push for our Q3 signup campaign.", skills: ["Paid Social", "SEO", "A/B Testing"] },
  { id: "j8", title: "Product Designer", company: "Fenwick & Co", category: "Design", type: "One-off", duration: "Design sprint", budget: "$6,000 flat", location: "Remote", posted: "Jul 26, 2026", description: "Run a 2-week design sprint for a new onboarding flow.", skills: ["Figma", "UX Research", "Prototyping"] },
  { id: "j9", title: "Ops Coordinator", company: "Vantage Cloud", category: "Operations", type: "One-off", duration: "6 weeks", budget: "$3,200 flat", location: "Remote", posted: "Jul 22, 2026", description: "Stand up vendor management and internal process docs.", skills: ["Process Design", "Vendor Mgmt"] },
];

/* ----------------------------- talent profiles ---------------------------- */

const FREELANCER_PROFILES = {
  "katelin-rivera": {
    name: "Katelin Rivera",
    headline: "Senior Account Executive · Mid-Market B2B SaaS (Horizontal CRM)",
    location: "Manila, Philippines",
    yearsExp: 10,
    category: "Sales",
    skills: ["B2B SaaS Sales", "Horizontal CRM", "Mid-Market", "Full-Cycle Sales", "Salesforce", "HubSpot", "Negotiation", "Forecasting"],
    summary: "Account executive with 10+ years selling horizontal CRM software into mid-market B2B SaaS companies. I like building pipeline as much as closing it, and I've onboarded and mentored new AEs at every company I've worked at.",
    experience: [
      { role: "Senior Account Executive", company: "PipelinePro", period: "2021 — Present", desc: "Closing $2M+ ARR a year in mid-market deals for a horizontal CRM platform, consistently top 10% of the sales org." },
      { role: "Account Executive", company: "Vantage Cloud", period: "2018 — 2021", desc: "Owned full-cycle sales for mid-market SaaS accounts, growing a book of business from $0 to $850K ARR." },
      { role: "SDR → Account Executive", company: "Northwind Labs", period: "2015 — 2018", desc: "Started in SDR, promoted to AE within 18 months after consistently exceeding quota." },
    ],
  },
  "priya-nandan": {
    name: "Priya Nandan",
    headline: "Business Development Manager · Partnerships & Expansion",
    location: "Bengaluru, India",
    yearsExp: 7,
    category: "Business Development",
    skills: ["Partnerships", "Channel Sales", "Lead Generation", "Negotiation"],
    summary: "Business development manager focused on partner-led growth for B2B SaaS companies expanding into new markets.",
    experience: [
      { role: "Business Development Manager", company: "Solace Analytics", period: "2022 — Present", desc: "Built and ran the partner program from scratch, now 30% of new pipeline." },
      { role: "BD Associate", company: "Xentir Pte Ltd", period: "2019 — 2022", desc: "Sourced and closed regional channel partnerships across Southeast Asia." },
    ],
  },
  "marco-bellini": {
    name: "Marco Bellini",
    headline: "Frontend Engineer · React & TypeScript",
    location: "Milan, Italy",
    yearsExp: 6,
    category: "Tech",
    skills: ["React", "TypeScript", "CSS", "Design Systems"],
    summary: "Frontend engineer who's spent the last few years building and maintaining design systems for fast-moving product teams.",
    experience: [
      { role: "Frontend Engineer", company: "Fenwick & Co", period: "2020 — Present", desc: "Built and maintain the component library used across four product lines." },
    ],
  },
  "sena-okafor": {
    name: "Sena Okafor",
    headline: "Growth Marketer · Paid Social & SEO",
    location: "Lagos, Nigeria",
    yearsExp: 5,
    category: "Marketing",
    skills: ["Paid Social", "SEO", "A/B Testing", "Lifecycle Marketing"],
    summary: "Growth marketer focused on paid acquisition and lifecycle campaigns for early-stage SaaS.",
    experience: [
      { role: "Growth Marketer", company: "Vantage Cloud", period: "2023 — Present", desc: "Cut paid CAC by 34% in the first two quarters through channel reallocation." },
    ],
  },
};

// Cosmetic display fields (country, status) for the company dashboard's
// freelancer table. The backend has its own copy for validating payment
// recipients (backend/demo_users.py) — that copy is the one that's actually
// authoritative; this one is just what's rendered on screen.
const SAMPLE_FREELANCERS = [
  { name: "Katelin Rivera", country: "Philippines", status: "Active" },
  { name: "Priya Nandan", country: "India", status: "Active" },
  { name: "Marco Bellini", country: "Italy", status: "Active" },
  { name: "Sena Okafor", country: "Nigeria", status: "Pending onboarding" },
];

/* -------------------------------- toast -------------------------------- */

function showToast(message) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

/* -------------------------------- modal -------------------------------- */

function openModal(id) {
  document.getElementById(id).classList.add("open");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

/* ------------------------------- safe DOM -------------------------------
   Build table rows with textContent instead of innerHTML string interpolation
   so that if a name/memo/etc. ever comes from real (untrusted) user input,
   it can't inject markup into the page. */

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  }
  for (const child of children) {
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

/* -------------------------------------------------------------------------
   Descope Web Component mount helper.
   Call this on the login pages after the <descope-wc> tag exists in the DOM.
   If the real Descope script hasn't loaded (e.g. you haven't set your
   Project ID yet), we fall back to a placeholder with a "continue without
   signing in" button so you can still click through the rest of the app
   while the flow is still being built.
   ------------------------------------------------------------------------- */

function mountDescopeFlow({ flowId, onComplete, mountId = "flow-mount" }) {
  const wcExists = customElements.get("descope-wc");
  const mount = document.getElementById(mountId);
  const isPlaceholderId = DESCOPE_PROJECT_ID === "YOUR_DESCOPE_PROJECT_ID";

  if (wcExists && !isPlaceholderId) {
    const wc = document.createElement("descope-wc");
    wc.setAttribute("project-id", DESCOPE_PROJECT_ID);
    wc.setAttribute("flow-id", flowId);
    wc.setAttribute("theme", "light");
    mount.innerHTML = "";
    mount.appendChild(wc);

    wc.addEventListener("success", (e) => {
      // The session JWT the Web Component hands back on success. We only use
      // it as a bearer token to send to our own backend — the backend
      // re-validates it independently and is the one that decides identity
      // and role, so we don't need to (and don't) trust anything else in
      // this payload for authorization purposes.
      const detail = (e && e.detail) || {};
      const sessionJwt = detail.sessionJwt || (detail.data && detail.data.sessionJwt) || detail.token;
      const user = detail.user || {};

      if (!sessionJwt) {
        console.error("Descope success event had no session JWT in e.detail — check the shape below and adjust mountDescopeFlow():", detail);
      }
      SessionToken.set(sessionJwt, user.name || user.email || "");
      onComplete(user.name || user.email || "there");
    });

    wc.addEventListener("error", (err) => {
      console.error("Descope flow error", err);
      const isStepUp = flowId === WITHDRAW_STEP_UP_FLOW_ID || flowId === BANK_LINK_STEP_UP_FLOW_ID;
      if (isStepUp) {
        showToast("Step-up verification needs a real signed-in session. If you used “Continue without signing in,” sign out and sign in for real first.");
      } else {
        showToast("Something went wrong with the sign-in flow — check the console.");
      }
    });
  } else {
    // No live Descope project wired up yet — show a placeholder + bypass.
    mount.innerHTML = `
      <div class="placeholder-copy">
        <p><strong>Descope flow not connected yet.</strong></p>
        <p>Set <code>DESCOPE_PROJECT_ID</code> and <code>${
          flowId === FREELANCER_FLOW_ID ? "FREELANCER_FLOW_ID" : "COMPANY_FLOW_ID"
        }</code> in <code>js/app.js</code> to embed your real flow (id: <code>${flowId}</code>) here.</p>
      </div>
    `;
  }
}
