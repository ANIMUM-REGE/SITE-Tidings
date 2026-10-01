#!/usr/bin/env python3
"""Real-browser check of the homepage phone → /get/ → store hop (BB 2026-10-01).

Serves this repo on localhost, drives Chromium (Playwright) with real phone/desktop user agents,
and intercepts the two store hosts so nothing leaves the machine. Needs `pip install playwright`
+ `playwright install chromium` (or PW_CHANNEL=chrome to use an installed Chrome).

Usage: python3 scripts/test_root_redirect.py   (exit 1 on any failure)
"""
import functools
import http.server
import os
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
          "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
ANDROID = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/124.0 Mobile Safari/537.36")
DESKTOP = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/124.0 Safari/537.36")
GOOGLEBOT = ("Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, "
             "like Gecko) Chrome/124.0 Mobile Safari/537.36 (compatible; Googlebot/2.1; "
             "+http://www.google.com/bot.html)")
APP_STORE = "https://apps.apple.com/app/id6790977142"
PLAY = "https://play.google.com/store/apps/details?id=com.animumrege.tidings"


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{httpd.server_port}"


def stub_stores(context):
    for host in ("https://apps.apple.com/**", "https://play.google.com/**"):
        context.route(host, lambda route: route.fulfill(status=200, body="store"))


def final_url(browser, base, path, ua, touch=False, via_internal_link=False):
    context = browser.new_context(user_agent=ua, has_touch=touch)
    if touch:  # real iPhones/iPads report 5; Chrome's emulation reports 1 (the iPadOS check is > 1)
        context.add_init_script("Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 5})")
    stub_stores(context)
    page = context.new_page()
    if via_internal_link:  # e.g. back to the homepage from the privacy page (same-origin referrer)
        page.goto(base + "/privacy.html")
        page.evaluate("p => { const a = document.createElement('a'); a.href = p; "
                      "document.body.appendChild(a); a.click(); }", path)
        page.wait_for_load_state("load")
    else:
        page.goto(base + path)
    page.wait_for_timeout(400)  # let any location.replace chain settle
    url = page.url
    context.close()
    return url


def main() -> int:
    base = serve()
    cases = [
        # (label, path, ua, touch, via_internal_link, expected final URL — prefix match)
        ("iPhone tapping the 1.3.13 invite link", "/", IPHONE, True, False, APP_STORE),
        ("Android tapping the 1.3.13 invite link", "/", ANDROID, True, False, PLAY),
        ("Android with ?ref= keeps the Play referrer", "/?ref=ABCD2345", ANDROID, True, False,
         PLAY + "&referrer=ref%3DABCD2345"),
        ("iPadOS (desktop-class UA + touch)", "/", DESKTOP.replace("Chrome/124.0 ", ""), True, False,
         APP_STORE),
        ("desktop stays on the homepage", "/", DESKTOP, False, False, base + "/"),
        ("phone navigating within the site stays", "/", IPHONE, True, True, base + "/"),
        ("smartphone crawler stays (search/preview)", "/", GOOGLEBOT, False, False, base + "/"),
        ("/get/ itself still routes iPhone", "/get/", IPHONE, True, False, APP_STORE),
        ("/get/ itself still routes Android", "/get/", ANDROID, True, False, PLAY),
    ]
    failures = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=os.environ.get("PW_CHANNEL") or None)
        for label, path, ua, touch, internal, want in cases:
            got = final_url(browser, base, path, ua, touch, internal)
            ok = got == want if want.startswith(base) else got.startswith(want)
            failures += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {label}: {path} -> {got}")
        # The homepage CTA goes straight to /get/ (was /trial/ → /get/, one extra hop).
        context = browser.new_context(user_agent=DESKTOP)
        page = context.new_page()
        page.goto(base + "/")
        cta = page.get_attribute("a.btn", "href")
        ok = cta == "/get/"
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  homepage CTA href: {cta}")
        browser.close()
    print(f"{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
