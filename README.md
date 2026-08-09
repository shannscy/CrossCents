# CrossCents

CrossCents is a marketplace for one-off and short-term work. Companies post
jobs; freelancers build a profile — skills and experience, no rates to
market — and apply. Payment runs through the platform itself once a contract is signed,
across borders, without the wait. This repo is the front-end: the UI, the
auth surfaces, and the sign-in flows everything else gets built around.

## Current state

- **Built:** the login pages (`freelancer-login.html`, `company-login.html`)
  are wired to embed Descope's Web Component. Once you set your Project ID
  and Flow IDs, clicking "sign in" launches your real Descope flow.
- **Not yet built:** job listings, talent profiles, balances, transactions,
  and the "send payment" / "withdraw" / "post a job" actions currently run
  on sample data in `js/app.js` — there's no backend or ledger behind them
  yet. Those screens exist to give the auth moments (login, step-up
  verification) a real context to sit in while the rest of the product
  gets built out.

## File structure

```
index.html                  landing page — hero, search, categories, how it works
about.html                   CrossCents summary + founder bio
contact.html                 contact form (business email / phone)
chat.html                     mocked chat-with-us widget
freelancer-login.html        Descope flow embed — freelancer sign-up/in
freelancer-jobs.html         job marketplace — search, category filter, apply + sign contract
freelancer-profile.html      Katelin Rivera's profile — skills, experience, bio
freelancer-dashboard.html    balance, transactions, withdraw (step-up), link bank (step-up)
company-login.html           Descope flow embed — company admin sign-in (MFA)
company-talent.html          browse/search freelancer profiles
company-post-job.html        post a job + your posted jobs
company-dashboard.html       freelancer list, send payment
css/styles.css               shared styling
js/app.js                    sample data (jobs, profiles), session handling, Descope mount helper
```

## Running it

These are static files — no build step. Two ways to view:

1. **Quick look, no Descope wired up yet:** just double-click `index.html`
   to open it in a browser. Everything works except the two login pages,
   which will show a "Descope flow not connected yet" placeholder with a
   **Continue without signing in** button so you can still click through
   the rest of the app.

2. **Once you wire up Descope:** serve the folder over `http://` rather
   than opening it as a `file://` path — the Descope Web Component and any
   OAuth/redirect-based steps in your flow generally need a real origin.
   From inside the `crosscents` folder:

   ```bash
   npx serve .
   # or
   python3 -m http.server 8080
   ```

   Then open `http://localhost:.../index.html`.

## Wiring up your Descope project

1. In the [Descope console](https://app.descope.com), build two flows:
   - A **freelancer** flow: passwordless (email OTP or magic link), maybe
     a social login option. Low friction — this is just "can I see my
     balance."
   - A **company admin** flow: something higher-assurance at login itself
     (e.g. email/password or OTP *plus* an MFA step), since a company
     admin's first action in the app is capable of sending money.
2. Copy your **Project ID** from Project Settings.
3. Open `js/app.js` and set:
   ```js
   const DESCOPE_PROJECT_ID = "your-real-project-id";
   const FREELANCER_FLOW_ID = "your-freelancer-flow-id";
   const COMPANY_FLOW_ID = "your-company-flow-id";
   ```
4. On each login page (`freelancer-login.html`, `company-login.html`), the
   `<head>` currently has a generic CDN `<script>` tag for the Web
   Component. Descope's console shows you the exact, version-pinned script
   tag under your flow's **"Get Code"** panel — swap that in instead of
   trusting a hardcoded version here, since package versions change.
5. Reload the login page. If everything's wired correctly, the dashed
   placeholder box is replaced by your real Descope flow, and completing
   it redirects into the matching dashboard.

The `success` event handler in `mountDescopeFlow()` (in `js/app.js`) is
where the app should call `sdk.getSessionToken()` / `sdk.refresh()` from
the Descope Web JS SDK to get a real session. Right now it just reads
`e.detail.user` for a display name, since there's no backend here yet to
hand a session to.

## Where the Verif8 step-up would plug in

The **Withdraw funds** modal on the freelancer dashboard
(`freelancer-dashboard.html`) is deliberately built as a two-step
flow — enter an amount, then verify a 6-digit code — because that's the
natural home for a Verif8/8x8 CPaaS step-up. It's not wired up yet (any
code "works" for now). Two realistic ways to build it:

- **Descope-orchestrated:** add a custom step/action to a dedicated
  "withdrawal verification" Descope flow that calls Verif8's SMS API to
  send the code, then uses Descope's OTP verification to confirm it before
  the app proceeds.
- **App-orchestrated:** call Verif8's Send SMS API directly from the
  backend for this step, then verify the code server-side before releasing
  the withdrawal — using Descope only for the original login, not this
  specific step.

Which one's "more correct" depends on how much of the verification logic
should live in Descope versus the app's own backend — worth deciding once
the backend exists.

## Notes

- Session state is a plain `localStorage` flag (`crosscents_session`) —
  it's there so navigating between the login and dashboard pages works
  correctly, not because it's secure. It should be replaced by real
  session/token handling once a backend is in place.
- No frameworks, no build tooling, on purpose — easy to read end to end in
  one sitting, and easy to swap pieces out as the product gets built out.
