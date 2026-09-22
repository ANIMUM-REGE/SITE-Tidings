# Fix: campaign-click beacon blocked by CORS (all browsers) — 2026-09-22

## Symptom (BB, verified)
Clicking `https://tidings.family/get/?c=ads-google` never increments the campaign counter
(`tidings-metrics.sh` / `/api/campaign/counts` stays 0). Fails identically on Safari, Chrome,
Opera, and a second computer — so NOT a local browser/blocker issue.

## Root cause (root-caused in a real browser via Playwright — this is definitive)
The `/get/` page fires the click as `navigator.sendBeacon(url, Blob(type:"application/json"))`.
- `sendBeacon` ALWAYS sends with credentials mode `include`.
- An `application/json` body is NOT a CORS-safelisted content-type → it forces a **preflight**.
- The Azure Function uses **platform-level CORS** (no CORS in code or host.json). Azure Functions
  platform CORS does NOT emit `Access-Control-Allow-Credentials: true`.
- With credentials `include`, the browser REQUIRES `Access-Control-Allow-Credentials: true` on the
  preflight response → it isn't there → **preflight fails, beacon is blocked** (`net::ERR_FAILED`).

Exact console error observed:
`Access to resource ... blocked by CORS policy: ... 'Access-Control-Allow-Credentials' header ...
is '' which must be 'true' when the request's credentials mode is 'include'.`

The server itself is fine — a direct POST records correctly. It is purely the browser CORS path.

## The fix (confirmed working against the LIVE server before this brief)
Make the beacon a CORS **simple request** so there is no preflight and no credentials requirement.
Change the content-type from `application/json` to `text/plain`. The server's `req.get_json()`
parses a text/plain body regardless of header — VERIFIED: a `Content-Type: text/plain` POST returned
HTTP 200 and incremented the counter. NO Azure/server change is needed; this is a static-site fix only.

In `get/index.html`, in the campaign-click IIFE:
1. `new Blob([body], { type: "application/json" })` → `new Blob([body], { type: "text/plain" })`
2. In the `fetch` fallback, change `headers: { "Content-Type": "application/json" }` →
   `headers: { "Content-Type": "text/plain" }` and add `credentials: "omit"` (keep `keepalive: true`).
   (A `text/plain` fetch with no other custom headers is also a simple request; `credentials:"omit"`
   belt-and-suspenders so it can never require Allow-Credentials.)

Leave everything else (slug allowlist, the redirect IIFE, ref forwarding) untouched.

## Deploy + verify (do not claim done until verified from the live surface)
1. Commit + push `SITE-Tidings` (GitHub Pages auto-deploys; give it a minute).
2. Confirm the DEPLOYED page carries `text/plain`:
   `curl -fsS https://tidings.family/get/?c=ads-google | grep -c 'text/plain'`  (expect >=1)
3. Prove a real browser click now lands. Preferred: use Playwright/Chrome MCP to navigate
   `https://tidings.family/get/?c=ads-meta` and confirm the POST to `/api/campaign/click` is 200
   (NOT net::ERR_FAILED) with no CORS console error. Use slug **ads-meta** for this test so it is
   distinguishable from prior test rows.
4. Cross-check the count moved:
   `curl -fsS -H "X-Admin-Token: <ask Marcus / TIDINGS_UNLOCK_ADMIN_TOKEN>" \
     https://tidings-backend-func.azurewebsites.net/api/campaign/counts`  (ads-meta should be >=1)

## Report back to the primary (Marcus) via iterm-send when done
- Commit SHA, deploy confirmed, and the before/after count for ads-meta proving a browser click lands.
- Note: the counter currently holds TEST rows only (ads-google=2, organic=1 from diagnosis) — real
  traffic is ~0. Do NOT try to delete storage rows (the estate classifier blocks cloud mass-delete);
  a proper zeroing is a separate follow-up if BB wants it.

## Notes
- Model tier: Tier 3 (well-scoped, verified fix). 
- Admin token for counts is in the vault as `TIDINGS_UNLOCK_ADMIN_TOKEN` — ask Marcus if needed.
