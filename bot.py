from playwright.sync_api import sync_playwright
import datetime
import random
import time
import signal
import sys

API_URL = "https://user.prismaxserver.com/api/daily-login-points"
WALLETS_FILE = "config.txt"
CYCLE_SECONDS = 24 * 60 * 60  # 24 jam

running = True

def handle_exit(sig, frame):
    global running
    print("\n[EXIT] Gracefully stopping bot...")
    running = False

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def load_wallets():
    with open(WALLETS_FILE) as f:
        return [x.strip() for x in f if x.strip()]

def run_one_cycle():
    wallets = load_wallets()
    today = datetime.date.today().strftime("%Y-%m-%d")

    print(f"\n[{datetime.datetime.now()}] Starting daily cycle")
    print(f"Loaded {len(wallets)} wallets\n")

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

        context.route(
            "**/*",
            lambda route, request:
                route.abort()
                if request.resource_type in ["image", "media", "font", "stylesheet"]
                else route.continue_()
        )

        page = context.new_page()
        page.goto("https://app.prismax.ai", wait_until="domcontentloaded")
        time.sleep(4)

        for wallet in wallets:
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
                    if d["already_claimed_daily"]:
                        print(f"[OK] {wallet} → already claimed | total {d['total_points']}")
                    else:
                        print(f"[CLAIMED] {wallet} +{d['points_awarded_today']} | total {d['total_points']}")
                else:
                    print(f"[FAIL] {wallet} → {result}")

            except Exception as e:
                print(f"[ERROR] {wallet} → {e}")

            time.sleep(random.uniform(4, 6))

        browser.close()

def sleep_until_next_cycle(start_time):
    elapsed = time.time() - start_time
    remaining = max(0, CYCLE_SECONDS - elapsed)

    print(f"\n[{datetime.datetime.now()}] Cycle done. Sleeping {int(remaining/60)} minutes")

    while remaining > 0 and running:
        time.sleep(min(60, remaining))
        remaining -= 60

def main_loop():
    print("[START] Prismax Daily Bot (24H MODE)")
    while running:
        start_time = time.time()
        run_one_cycle()
        sleep_until_next_cycle(start_time)

    print("[STOP] Bot stopped cleanly")

if __name__ == "__main__":
    main_loop()
