from playwright.sync_api import sync_playwright
import datetime
import random
import time
import signal
import sys

API_URL = "https://user.prismaxserver.com/api/daily-login-points"
WALLETS_FILE = "wallets.txt"
CYCLE_SECONDS = 24 * 60 * 60  # 24 jam

running = True

# ======================
# SIGNAL HANDLER
# ======================
def handle_exit(sig, frame):
    global running
    if running:
        print("\n[EXIT] Gracefully stopping bot...")
        running = False

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# ======================
# LOAD WALLETS
# ======================
def load_wallets():
    with open(WALLETS_FILE) as f:
        return [x.strip() for x in f if x.strip()]

# ======================
# RUN ONE DAILY CYCLE
# ======================
def run_one_cycle():
    global running

    wallets = load_wallets()
    today = datetime.date.today().strftime("%Y-%m-%d")

    print(f"\n[{datetime.datetime.now()}] Starting daily cycle")
    print(f"Loaded {len(wallets)} wallets\n")

    browser = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--disable-default-apps",
                    "--disable-blink-features=AutomationControlled",
                ]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                java_script_enabled=True,
            )

            # Block resource berat
            context.route(
                "**/*",
                lambda route, request:
                    route.abort()
                    if request.resource_type in ["image", "media", "font", "stylesheet"]
                    else route.continue_()
            )

            page = context.new_page()

            # Trigger Cloudflare
            page.goto("https://app.prismax.ai", wait_until="domcontentloaded")
            time.sleep(4)

            for wallet in wallets:
                if not running:
                    break

                payload = {
                    "wallet_address": wallet,
                    "chain": "solana",
                    "user_local_date": today
                }

                try:
                    result = page.evaluate(
                        """async ({url, data}) => {
                            const r = await fetch(url, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(data)
                            });
                            return await r.json();
                        }""",
                        {"url": API_URL, "data": payload}
                    )

                    if result.get("success"):
                        d = result["data"]
                        if d.get("already_claimed_daily"):
                            print(f"[OK] {wallet} → already claimed | total {d['total_points']}")
                        else:
                            print(f"[CLAIMED] {wallet} +{d['points_awarded_today']} | total {d['total_points']}")
                    else:
                        print(f"[FAIL] {wallet} → {result}")

                except KeyboardInterrupt:
                    print("\n[STOP] Interrupted during wallet processing")
                    running = False
                    break
                except Exception as e:
                    if not running:
                        break
                    print(f"[ERROR] {wallet} → {e}")

                time.sleep(random.uniform(4, 6))

    finally:
        if browser:
            try:
                browser.close()
            except:
                pass

# ======================
# SLEEP UNTIL NEXT CYCLE
# ======================
def sleep_until_next_cycle(start_time):
    elapsed = time.time() - start_time
    remaining = max(0, CYCLE_SECONDS - elapsed)

    print(f"\n[{datetime.datetime.now()}] Cycle done. Sleeping {int(remaining / 60)} minutes")

    try:
        while remaining > 0 and running:
            time.sleep(1)
            remaining -= 1
    except KeyboardInterrupt:
        print("\n[EXIT] Sleep interrupted by user")
        sys.exit(0)

# ======================
# MAIN LOOP
# ======================
def main_loop():
    print("[START] Prismax Daily Bot (24H MODE)")

    try:
        while running:
            start_time = time.time()
            run_one_cycle()
            if not running:
                break
            sleep_until_next_cycle(start_time)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[STOP] Bot stopped cleanly")
        sys.exit(0)

# ======================
# ENTRY POINT
# ======================
if __name__ == "__main__":
    main_loop()
