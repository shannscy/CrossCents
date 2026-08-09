# Deploying CrossCents

This is a static site (no build step, no server) — any static host works.
Two options below, both take under 2 minutes.

## Option A — GitHub Pages (recommended: free, permanent, easy to update)

1. Go to https://github.com/new, create a new **public** repo (e.g. `crosscents`). Don't add a README.
2. On the new repo's page, click **"uploading an existing file"** (or drag-and-drop
   this whole `crosscents` folder onto the page).
3. Drag all the files/folders from this package in (index.html, the login/dashboard
   pages, `css/`, `js/`, `favicon.svg`) and commit.
4. Go to **Settings → Pages**. Under "Build and deployment", set **Source: Deploy
   from a branch**, branch **main**, folder **/ (root)**. Save.
5. Wait ~1 minute, then your live URL appears at the top of that Pages settings
   screen — usually `https://<your-username>.github.io/crosscents/`.

To update later: edit files in the repo (or re-upload) and it redeploys automatically.

## Option B — Netlify Drop (fastest, no account needed to start)

1. Go to https://app.netlify.com/drop
2. Drag this whole `crosscents` folder onto the page.
3. You'll get a live URL immediately (like `random-name.netlify.app`).
4. Optional: create a free Netlify account afterward to "claim" the site so it
   doesn't expire and so you can rename the subdomain or attach a custom domain.

## Notes

- Everything here is static HTML/CSS/JS — no environment variables, no server,
  nothing to configure for hosting itself.
- The two login pages will only show real sign-in once you wire up a Descope
  project ID (see the main README.md) — until then they fall back to a
  "continue as demo" button, which is fine for showing the app off.
- If you want a custom domain later (e.g. crosscents.app), both GitHub Pages
  and Netlify support adding one for free once you own the domain.
