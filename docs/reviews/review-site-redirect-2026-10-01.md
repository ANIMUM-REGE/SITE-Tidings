# Review: Homepage phone→/get/ redirect (PR #1, head af9acc9)

**Reviewer:** review-tidings-site (adversarial, read-only)
**Date:** 2026-10-01
**Target:** https://github.com/ANIMUM-REGE/SITE-Tidings/pull/1, branch `fix/root-mobile-to-get` @ `af9acc9`

## Verdict: SHIP

The core redirect logic (`index.html`'s inline script) behaves correctly for every scenario
tested, including the PR's own 10/10 Playwright suite re-run locally plus additional adversarial
cases below. No redirect loop, no dead end, no SEO/preview regression, no wrongly-redirected
desktop. The findings below are real but narrow: one latent gap (hash fragments) that nothing in
the current app relies on yet, a lint script with a few blind spots, and a process gap (no CI).
None block merging this PR; two are worth a fast follow-up.

## Findings (ranked)

### 1. [MEDIUM] `check_links.py` misses scheme-less and mixed-case bare-root links
`scripts/check_links.py:18` — `BARE = re.compile(r"https?://(?:www\.)?tidings\.family(?![\w-]|\.\w)(?!/[\w.-])")`, no `re.IGNORECASE`, and requires a `https?://` prefix.

Verified misses (regex tested directly against the compiled pattern):
```
False | Learn more at tidings.family today      # scheme-less mention
False | HTTPS://TIDINGS.FAMILY                   # uppercase
False | https://TIDINGS.family/                  # mixed-case host
True  | http://tidings.family                    # (correctly caught, for contrast)
```
**Scenario:** marketing/support copy that writes the bare domain without a scheme (very common
phrasing, e.g. "Learn more at tidings.family" in a future `support.html` edit or app-copy file
that isn't `.md`), or a link whose host happens to be upper/mixed case (copy-pasted from a mail
client or CMS that title-cases), ships silently — `check_links.py` exits 0 and nothing blocks the
merge. This is exactly the class of bug the script exists to catch (the 1.3.13 invite text that
started this PR was precisely a bare-root mention, if it had been scheme-less or differently cased
this script would not have caught a repeat).

No false positives found in the other direction: `/get/...`, `/privacy.html`, `tidings.family.com`,
and the CNAME file's bare domain (not a hyperlink) are all correctly left alone, and the script's
own docstring text about itself no longer trips it (confirmed, exit 0 on current tree).

**Fix:** add `re.IGNORECASE`, and either also match scheme-less `(?<![\w/.-])tidings\.family` mentions
outside URLs, or accept the scheme-less gap explicitly in the docstring so it's a documented
limitation rather than a silent one.

### 2. [MEDIUM] Hash fragment is dropped on the mobile → `/get/` hop
`index.html:20` — `location.replace("/get/" + location.search);` uses only `location.search`; `location.hash` is never forwarded.

Verified by instrumenting the local server's request log: navigating to `/?c=sms#section2` on an
iPhone UA produced a server request for `/get/?c=sms` only — the `#section2` fragment never reached
`/get/` (confirmed again with a hash-only URL, `/#ref=ABCD2345`, which redirects through with no ref
at all).

**Scenario:** today this is latent, not active — both `?ref=` and `?c=` are query parameters, never
carried in a fragment, so no current link breaks. But it's an unannounced constraint: any future
link-shortener, SMS-tracking service, or email-wrapper that appends state after `#` (some do, to
avoid it being sent to the server) will silently lose that state on a phone tapping the homepage,
with no error, no log, just a redirect to `/get/` missing the parameter. Worth a one-line comment
next to `index.html:20` documenting that `location.hash` is intentionally dropped (or forwarding it
if that's not intentional) so a future editor doesn't get surprised the same way the 1.3.13 bare-link
issue surprised this one.

### 3. [LOW] No CI enforcement of either new check
No `.github/workflows/` directory exists in this repo, and no git hooks are installed
(`.git/hooks` has only the `*.sample` files). `scripts/check_links.py` and
`scripts/test_root_redirect.py` are real, useful, and both pass — but nothing runs them
automatically. They're invoked by hand (per the PR description) before merge.

**Scenario:** this repo deploys to production the moment a PR merges to `main` via GitHub Pages
(per the brief). A future PR that reintroduces a bare-root link, or a future homepage edit that
breaks the referrer/UA check, merges clean with no automated signal — the only backstop is whoever
is reviewing remembering to run both scripts locally. Given finding #1 shows the lint script
already has blind spots a reviewer is unlikely to catch by eye, this raises the cost of a repeat.
Not a blocker for this PR; worth a fast follow-up to wire both scripts into a GitHub Actions check
on `pull_request`.

### 4. [INFO, confirmed not a bug] Once redirected, a phone can't reach the homepage again through normal navigation
Per the brief's question — verified:
- **Back button:** confirmed. `location.replace` replaces the history entry for `/` itself, so `/`
  never exists as a distinct entry; there's nothing to go "back" to.
- **Any in-site link back to `/`:** none exists. Grepped every page (`privacy.html`, `support.html`,
  `sms-opt-in.html`, `get/`, `trial/`, `unlock/`) for an `href` pointing at the root — none found.
- **Retyping the URL:** a typed/bookmarked navigation sends no referrer, so the same-origin check at
  `index.html:19` doesn't fire, and the phone is redirected again.
- **"Request Desktop Site" (iOS Safari):** also doesn't help — it changes the UA to the same
  Mac-style string iPadOS already sends, which still matches the `mac && maxTouchPoints > 1` branch
  (a real device still reports touch), so redirect still fires.

Net effect: a phone visitor cannot see the homepage HTML at all, ever, short of disabling JS. This
matches the PR description's own stated blast radius ("phones arriving from outside the site go to
the store instead of the homepage") and is clearly the intended design, not a defect — flagging it
only because the brief asked, and because it's worth knowing for support/QA purposes (e.g. "open
tidings.family on your phone to see X" will no longer work as a support instruction).

### 5. [INFO] `/terms` and a custom `/404` don't exist, so they're moot
No `terms*` page and no repo-root `404.html` exist in this site. GitHub Pages serves its stock,
unbranded 404 for any unmatched path (including a hypothetical `/terms`) — a static page with no
JS, so it can't loop or interact with the new redirect logic either way. Out of scope for this PR,
noted only to close out the brief's checklist.

## What held up under attack (verified, not just read)

- **Redirect loop / dead end:** none. `/get/` never redirects back to `/`; it either sends iOS/Android
  straight to their store or (desktop/unrecognized UA) shows the static fallback with real badge
  links. Re-ran the PR's own suite plus manual cases — 10/10 pass on this branch:
  ```
  PASS  iPhone tapping the 1.3.13 invite link: / -> https://apps.apple.com/app/id6790977142
  PASS  Android tapping the 1.3.13 invite link: / -> https://play.google.com/store/.../tidings
  PASS  Android with ?ref= keeps the Play referrer: /?ref=ABCD2345 -> ...&referrer=ref%3DABCD2345
  PASS  iPadOS (desktop-class UA + touch): / -> https://apps.apple.com/app/id6790977142
  PASS  desktop stays on the homepage
  PASS  phone navigating within the site stays
  PASS  smartphone crawler stays (search/preview)
  PASS  /get/ itself still routes iPhone
  PASS  /get/ itself still routes Android
  PASS  homepage CTA href: /get/
  0 failure(s)
  ```
- **`?ref=`/`?c=` survive the hop exactly**, including encoding — confirmed via the `?ref=` referrer
  test above and by direct request capture (`/get/?c=sms` requested verbatim, no mangling).
- **In-app browsers / stripped referrer / Custom Tabs / typed URLs:** all share the same mechanism —
  no same-origin `document.referrer` — so all correctly redirect to `/get/` as "arriving from
  outside," which is the desired behavior for the invite-link bug this PR fixes. (Verified by code
  logic and by the "iPhone tapping the invite link" case, which is referrer-less exactly like an
  in-app-browser tap; could not exercise real iMessage/WhatsApp/Instagram apps in this sandbox.)
- **Desktop with a touchscreen is not wrongly redirected:** tested a Windows/Chrome UA with
  `maxTouchPoints = 10` — stays on the homepage, confirmed live:
  ```
  Windows touchscreen -> http://127.0.0.1:<port>/
  ```
- **Link previews / SEO:** unaffected, for a stronger reason than the UA bot-list suggests — real
  preview fetchers (WhatsApp, iMessage's LinkPresentation, Slack, Twitter/X, Facebook) overwhelmingly
  fetch raw HTML without executing JavaScript, so the redirect `<script>` never runs for them
  regardless of their UA string; the `/bot|crawl|spider|preview/i` check is a defensive second layer,
  not the only one. The one crawler class that *does* execute JS for indexing (Googlebot's evergreen
  renderer) self-identifies with "bot" in its UA and is correctly excluded — tested directly. No
  `noindex` was added to the homepage; `/get/` already carried `noindex,nofollow` before this PR and
  still does.
- **`check_links.py` false positives:** none found. `/get/`, `/privacy.html`, `tidings.family.com`,
  and the CNAME file's bare domain are all correctly left alone; the script's own text no longer
  trips itself (the exact thing af9acc9 fixed) — confirmed, clean exit 0 on the current tree.

## Scope note
Read-only review. No site code, branch, or PR touched other than this new file on this new branch.
