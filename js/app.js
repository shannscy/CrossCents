/* CrossCents — shared demo logic
   -----------------------------------------------------------------------
   This is a MOCK app. There is no real backend, no real bank, no real
   money movement. Its only real piece of plumbing is the Descope Flow
   embed on the two login pages (freelancer-login.html / company-login.html).

   HOW TO WIRE UP YOUR REAL DESCOPE PROJECT:
   1. Create your flows in the Descope console (console.descope.com).
   2. Copy your Project ID from Project Settings.
   3. Fill in the three constants below.
   4. On each login page, the Descope console's "Get Code" panel for your
      flow will give you the exact <script> / CDN version to paste into
      the <head> — versions change, so copy that snippet directly rather
      than trusting a hardcoded version number here.
   ----------------------------------------------------------------------- */

const DESCOPE_PROJECT_ID = "YOUR_DESCOPE_PROJECT_ID"; // <-- replace me
const FREELANCER_FLOW_ID = "sign-up-or-in";            // <-- your freelancer flow id
const COMPANY_FLOW_ID = "company-admin-login";          // <-- your company/admin flow id

/* ---------------------------- mock session ---------------------------- */

const Session = {
  set(role, name, org) {
    localStorage.setItem(
      "crosscents_session",
      JSON.stringify({ role, name, org: org || null, at: "demo" })
    );
  },
  get() {
    const raw = localStorage.getItem("crosscents_session");
    return raw ? JSON.parse(raw) : null;
  },
  clear() {
    localStorage.removeItem("crosscents_session");
  },
  requireRole(role, redirectTo) {
    const s = Session.get();
    if (!s || s.role !== role) {
      window.location.href = redirectTo;
    }
    return s;
  },
};

function logout(redirectTo) {
  Session.clear();
  window.location.href = redirectTo || "index.html";
}

/* ------------------------------ mock data ------------------------------ */

const MOCK_TRANSACTIONS = [
  { company: "Xentir Pte Ltd", amount: 1200, date: "Aug 4, 2026", status: "complete" },
  { company: "Northwind Labs", amount: 850, date: "Jul 28, 2026", status: "complete" },
  { company: "Xentir Pte Ltd", amount: 430, date: "Jul 14, 2026", status: "pending" },
  { company: "Fenwick & Co", amount: 2100, date: "Jul 2, 2026", status: "complete" },
];

const MOCK_FREELANCERS = [
  { name: "Alex Rivera", country: "Philippines", lastPaid: "Aug 4, 2026", status: "Active" },
  { name: "Priya Nandan", country: "India", lastPaid: "Jul 30, 2026", status: "Active" },
  { name: "Marco Bellini", country: "Italy", lastPaid: "Jul 22, 2026", status: "Active" },
  { name: "Sena Okafor", country: "Nigeria", lastPaid: "-", status: "Pending onboarding" },
];

function formatCurrency(n) {
  return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

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

/* -------------------------------------------------------------------------
   Descope Web Component mount helper.
   Call this on the login pages after the <descope-wc> tag exists in the DOM.
   If the real Descope script hasn't loaded (e.g. you haven't set your
   Project ID yet), we fall back to a visible "Demo mode" button so you can
   still click through the rest of the app while your Descope flow is a
   work in progress.
   ------------------------------------------------------------------------- */

function mountDescopeFlow({ flowId, onComplete }) {
  const wcExists = customElements.get("descope-wc");
  const mount = document.getElementById("flow-mount");
  const isPlaceholderId = DESCOPE_PROJECT_ID === "YOUR_DESCOPE_PROJECT_ID";

  if (wcExists && !isPlaceholderId) {
    const wc = document.createElement("descope-wc");
    wc.setAttribute("project-id", DESCOPE_PROJECT_ID);
    wc.setAttribute("flow-id", flowId);
    wc.setAttribute("theme", "light");
    mount.innerHTML = "";
    mount.appendChild(wc);

    wc.addEventListener("success", (e) => {
      // e.detail typically carries the authenticated user's info once the
      // flow completes. Real session/JWT handling should use the Descope
      // Web JS SDK (sdk.getSessionToken() / sdk.refresh()) rather than
      // this mock — see README for the real integration notes.
      const user = (e.detail && e.detail.user) || {};
      onComplete(user.name || user.email || "there");
    });

    wc.addEventListener("error", (err) => {
      console.error("Descope flow error", err);
      showToast("Something went wrong with the sign-in flow — check the console.");
    });
  } else {
    // No live Descope project wired up yet — show a placeholder + demo bypass.
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

function demoBypassLogin(name) {
  document.getElementById("demo-name")?.blur();
  const input = document.getElementById("demo-name-input");
  const finalName = (input && input.value.trim()) || name;
  document.dispatchEvent(new CustomEvent("crosscents:demo-login", { detail: finalName }));
}
