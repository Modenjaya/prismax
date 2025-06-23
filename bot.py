import requests
import datetime
import json
import time
import os

# --- KONFIGURASI ---
# Nama file konfigurasi tempat alamat-alamat wallet disimpan
CONFIG_FILE = "config.txt"

# URL API Check-in
API_URL = "https://app-prismax-backend-1053158761087.us-west2.run.app/api/daily-login-points"

# Waktu jeda antara setiap siklus check-in untuk semua akun (dalam detik)
# 24 jam = 24 * 60 * 60 = 86400 detik
CHECK_IN_INTERVAL_SECONDS = 86400 

# Jeda antara setiap akun dalam satu siklus (disarankan untuk menghindari throttling)
DELAY_BETWEEN_WALLETS_SECONDS = 5 

def load_wallet_addresses(config_file):
    """
    Memuat daftar alamat wallet dari file konfigurasi.
    Setiap baris di file dianggap sebagai satu alamat wallet.
    """
    wallet_addresses = []
    try:
        with open(config_file, 'r') as f:
            for line in f:
                address = line.strip() # Hapus spasi di awal/akhir dan newline
                if address and not address.startswith('#'): # Pastikan bukan baris kosong atau komentar
                    wallet_addresses.append(address)
        if not wallet_addresses:
            print(f"ERROR: No wallet addresses found in '{config_file}'. Please add them, one per line.")
            return None
        return wallet_addresses
    except FileNotFoundError:
        print(f"ERROR: Configuration file '{config_file}' not found. Please create it and add your WALLET_ADDRESSes.")
        return None
    except Exception as e:
        print(f"ERROR: An error occurred while reading '{config_file}': {e}")
        return None

# --- FUNGSI BOT ---
def perform_daily_checkin(wallet_address):
    """
    Melakukan permintaan check-in harian ke API Prismax AI untuk satu alamat wallet.
    """
    today = datetime.date.today()
    user_local_date = today.strftime("%Y-%m-%d")

    headers = {
        "Content-Type": "application/json",
        "Origin": "https://app.prismax.ai",
        "Referer": "https://app.prismax.ai/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36" 
    }

    payload = {
        "wallet_address": wallet_address,
        "user_local_date": user_local_date
    }

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Attempting daily check-in for wallet: {wallet_address} on date: {user_local_date}")

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Akan memunculkan HTTPError untuk status kode 4xx/5xx
        result = response.json()

        if result.get("success"):
            data = result.get("data", {})
            if data.get("already_claimed_daily"):
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SUCCESS [{wallet_address}]: Already claimed daily check-in for today. Total points: {data.get('total_points')}")
            else:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SUCCESS [{wallet_address}]: Daily check-in complete! Points awarded today: {data.get('points_awarded_today')}. Total points: {data.get('total_points')}")
        else:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FAILED [{wallet_address}]: API returned success=false. Message: {result.get('message', 'No message provided')}")
            print(f"Response: {result}")

    except requests.exceptions.HTTPError as errh:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] HTTP Error [{wallet_address}]: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connection Error [{wallet_address}]: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Timeout Error [{wallet_address}]: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] An unexpected error occurred [{wallet_address}]: {err}")
    except json.JSONDecodeError:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FAILED [{wallet_address}]: Could not decode JSON response. Response text: {response.text}")

if __name__ == "__main__":
    while True: # Loop utama agar skrip berjalan terus-menerus
        wallet_addresses = load_wallet_addresses(CONFIG_FILE)
        if wallet_addresses:
            print(f"\n--- [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting daily check-in cycle for {len(wallet_addresses)} wallet(s). ---")
            for i, address in enumerate(wallet_addresses):
                perform_daily_checkin(address)
                if i < len(wallet_addresses) - 1: # Jangan tidur setelah wallet terakhir
                    # Jeda antara setiap akun dalam satu siklus
                    time.sleep(DELAY_BETWEEN_WALLETS_SECONDS) 
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] All wallet check-ins attempted for this cycle.")
        else:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No wallets loaded. Retrying after interval.")

        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Waiting for {CHECK_IN_INTERVAL_SECONDS / 3600:.1f} hours ({CHECK_IN_INTERVAL_SECONDS} seconds) before next cycle...")
        time.sleep(CHECK_IN_INTERVAL_SECONDS) # Jeda panjang sebelum siklus berikutnya
