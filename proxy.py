# proxy_test.py
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import os, random, string, traceback

# --- Load .env from this file's directory and override any system env vars ---
HERE = Path(__file__).parent
load_dotenv(dotenv_path=HERE / ".env", override=True)

HOST = (os.getenv("HOST") or "brd.superproxy.io").strip()
PORT = (os.getenv("PORT") or "33335").strip()
BASE_USER = (os.getenv("USERNAME") or "").strip()   # e.g. brd-customer-...-zone-freemium
PASSWORD = (os.getenv("PASSWORD") or "").strip()

print("DEBUG .env loaded from:", (HERE / ".env"))
print("DEBUG HOST :", HOST)
print("DEBUG PORT :", PORT)
print("DEBUG USER :", BASE_USER)     # should be brd-customer-...-zone-freemium
print("DEBUG PASS :", f"<{len(PASSWORD)} chars>")

if not BASE_USER or not PASSWORD:
    raise SystemExit("ERROR: USERNAME or PASSWORD missing. Fix your .env.")

def session_user(base: str) -> str:
    s = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{base}-session-{s}"

def test_playwright():
    print("\n=== Playwright proxy test ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            proxy={
                "server": f"http://{HOST}:{PORT}",
                "username": session_user(BASE_USER),
                "password": PASSWORD,
            },
            ignore_https_errors=True,
        )
        page = context.new_page()

        urls = [
            "https://geo.brdtest.com/welcome.txt?product=dc&method=native",
            "https://geo.brdtest.com/mygeo.json",
        ]

        try:
            for url in urls:
                print("\n-> GET", url)
                resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                if resp is None:
                    print("No response object (navigation likely blocked).")
                    continue
                print("HTTP:", resp.status)
                text = page.text_content() or ""
                print("Body snippet:", (text[:300] + ("..." if len(text) > 300 else "")))
        except Exception as e:
            print("Playwright exception:", repr(e))
            traceback.print_exc()
        finally:
            context.close()
            browser.close()

def test_httpx():
    print("\n=== HTTPX proxy test (optional) ===")
    try:
        import httpx
    except ImportError:
        print("httpx not installed. Run:  pip install httpx")
        return

    proxies = f"http://{BASE_USER}:{PASSWORD}@{HOST}:{PORT}"
    print("HTTPX proxies:", proxies.replace(PASSWORD, "<hidden>"))

    try:
        with httpx.Client(proxies=proxies, timeout=20.0, verify=False) as client:
            r = client.get("https://geo.brdtest.com/welcome.txt?product=dc&method=native")
            print("HTTP:", r.status_code)
            print("Body snippet:", (r.text[:300] + ("..." if len(r.text) > 300 else "")))
    except Exception as e:
        print("HTTPX exception:", repr(e))
        traceback.print_exc()

if __name__ == "__main__":
    test_playwright()
    test_httpx()
    print("\nDone.")

