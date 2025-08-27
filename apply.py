# apply.py (speed-tuned)
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import os, re, time, random, string

URL = "https://support.pearlabyss.com/en-us/Research?_id=7a5df52b448ca838dda27ae717aba1fa1b569e04fba8e5e0dba88d69425f7570"

HERE = Path(__file__).parent
load_dotenv(dotenv_path=HERE / ".env", override=True)

USERNAME = (os.getenv("USERNAME") or "").strip()   # brd-customer-...-zone-freemium
PASSWORD = (os.getenv("PASSWORD") or "").strip()
HOST     = (os.getenv("HOST") or "brd.superproxy.io").strip()
PORT     = (os.getenv("PORT") or "33335").strip()

REGION      = (os.getenv("REGION") or "Europe").strip()
HEADLESS    = (os.getenv("HEADLESS") or "0").lower() in ("1","true","yes")
ROTATE_PER  = int(os.getenv("ROTATE_PER", "0"))     # 0 = never rotate (fastest)
BLOCK_MEDIA = (os.getenv("BLOCK_MEDIA") or "1").lower() in ("1","true","yes")

NAMES_FILE = HERE / "names.txt"
with open(NAMES_FILE, encoding="utf-8") as f:
    NAMES = [line.strip() for line in f if line.strip()]

# ---------- helpers ----------
def _rand_session(k: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))

def build_proxy_username():
    if not USERNAME or not PASSWORD:
        return None
    country = "-country-eu" if REGION.lower().startswith("euro") else "-country-us"
    return f"{USERNAME}{country}-session-{_rand_session()}"

def make_discord_id(base: str) -> str:
    safe = re.sub(r'[^A-Za-z0-9]', '', base) or "user"
    candidates = [
        safe.lower(),
        safe.lower() + str(random.randint(1, 9999)),
        safe.lower() + "_" + str(random.randint(1, 99)),
        safe.lower() + random.choice(["x","xx","_",".","123","01","07"]),
        safe.lower()[:10] + "_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(2,4))),
    ]
    return random.choice(candidates)[:32]

def accept_cookies_if_present(page):
    for btn in ("Only Accept Required","Only accept required","Accept All","Accept all"):
        try:
            page.get_by_role("button", name=btn).click(timeout=1000)
            break
        except Exception:
            pass

def fill_and_submit(page, name: str):
    fam     = page.locator('input[name="_fieldData[0]._fieldValue"]')
    region  = page.locator('select[name="_fieldData[1]._fieldValue"]')
    disc    = page.locator('input[name="_fieldData[2]._fieldValue"]')
    consent = page.locator('input[name="_fieldData[3]._fieldValue"]')

    fam.fill(name)
    region.select_option(label=REGION)

    disc_id = make_discord_id(name)
    disc.fill(disc_id)
    print(f"  -> Discord ID: {disc_id}")

    # consent: label click, then JS fallback
    try:
        cid = consent.get_attribute("id")
        if cid:
            page.locator(f'label[for="{cid}"]').click()
    except Exception:
        pass
    if not consent.is_checked():
        page.evaluate(
            """(el) => {
                el.checked = true;
                el.dispatchEvent(new Event('input',  { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            consent
        )
    if not consent.is_checked():
        raise RuntimeError("Consent checkbox could not be checked")

    # wait only for the specific redirect; much faster than networkidle
    with page.expect_navigation(url=re.compile(r".*/Research/Complete.*"), timeout=12000):
        page.get_by_role("button", name=re.compile(r"Submit", re.I)).click()

def route_blocker_factory():
    # allowlist only what we need; block the rest (cuts a lot of 3rd-party latency)
    allow = (
        "https://support.pearlabyss.com/",
        "https://s1.pearlcdn.com/",
    )
    def blocker(route):
        req = route.request
        url = req.url
        if (url.startswith(allow[0]) or url.startswith(allow[1])):
            # Optionally block heavy resource types even on allowed hosts
            if BLOCK_MEDIA and req.resource_type in ("image","font","media"):
                return route.abort()
            return route.continue_()
        # block everything else (cookiebot, analytics, etc.)
        return route.abort()
    return blocker

# ---------- main ----------
def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)

        context = None
        page = None
        proxy_user = None
        used_in_batch = 0

        try:
            for idx, name in enumerate(NAMES, 1):
                # rotate proxy ONLY when ROTATE_PER > 0 and count hits that number
                rotate_now = ROTATE_PER > 0 and used_in_batch >= ROTATE_PER
                if context is None or rotate_now:
                    # close old
                    if page:
                        page.close()
                        page = None
                    if context:
                        context.close()
                        context = None
                    # new proxy (or reuse same if ROTATE_PER == 0 and context was None)
                    proxy_user = build_proxy_username() if ROTATE_PER != 0 else (proxy_user or build_proxy_username())
                    # build context once and reuse
                    kwargs = dict(
                        viewport={"width": 1366, "height": 768},
                        locale="en-US",
                        timezone_id="Europe/Vienna" if REGION.lower().startswith("euro") else "America/New_York",
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                        ignore_https_errors=True,
                    )
                    if proxy_user and PASSWORD:
                        kwargs["proxy"] = {
                            "server": f"http://{HOST}:{PORT}",
                            "username": proxy_user,
                            "password": PASSWORD,
                        }
                    context = browser.new_context(**kwargs)
                    context.route("**/*", route_blocker_factory())
                    used_in_batch = 0  # reset counter for this proxy

                # reuse the same page object to keep connections hot
                if page is None:
                    page = context.new_page()
                    # first nav (will show cookies once)
                    page.goto(URL, wait_until="domcontentloaded", timeout=20000)
                    accept_cookies_if_present(page)

                # log short session id
                session_id = proxy_user.split("-session-")[-1] if proxy_user else "none"
                print(f"Submitting form for: {name} via {session_id}")

                try:
                    # navigate back to form page if we're on the completion page
                    if "/Research/Complete" in page.url:
                        page.goto(URL, wait_until="domcontentloaded", timeout=20000)

                    fill_and_submit(page, name)
                    used_in_batch += 1

                except Exception as e:
                    print(f"[ERROR] {name}: {e}")
                    # Try to recover by forcing a reload of the form
                    try:
                        page.goto(URL, wait_until="domcontentloaded", timeout=20000)
                        accept_cookies_if_present(page)
                    except Exception:
                        pass

                # Your tiny jitter between submissions
                time.sleep(random.uniform(0.4, 0.7))

        finally:
            if page:
                page.close()
            if context:
                context.close()
            browser.close()

if __name__ == "__main__":
    run()

