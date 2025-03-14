import requests
import os
from collections import defaultdict

API_URL = os.getenv("API_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not API_URL:
    raise ValueError("API_URL tidak ditemukan di secret! Pastikan sudah diatur.")

def send_telegram_message(message):
    """Mengirim hasil pengecekan ke bot Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("📩 Notifikasi terkirim ke Telegram!")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Gagal mengirim notifikasi Telegram: {e}")

def country_flag(iso_code):
    """Mengonversi kode negara (ISO 3166-1 alpha-2) menjadi emoji bendera."""
    if iso_code == "Unknown":
        return "❓"
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso_code.upper())

def parse_proxy(proxy):
    return proxy.replace(",", ":")

def check_proxy(proxy):
    proxy = parse_proxy(proxy)
    try:
        ip, port = proxy.split(":")
    except ValueError:
        print(f"❌ Proxy format tidak valid: {proxy}")
        return (proxy, "Unknown", "Unknown", "Unknown", False, float("inf"))

    api_url = API_URL.format(ip=f"{ip}:{port}")

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Ambil nilai ping dari "delay"
        ping = data.get("delay", "9999 ms").replace(" ms", "")
        try:
            ping = float(ping)
        except ValueError:
            ping = float("inf")  # Jika gagal, anggap sebagai tidak valid

        status = data.get("proxyStatus", "").lower()
        country_code = data.get("countryCode", "Unknown")
        isp = data.get("isp", "Unknown")

        if "active" in status:
            print(f"✅ Proxy {ip}:{port} is ACTIVE (Ping: {ping} ms)")
            print(f"🔍 {ip}:{port} - {country_code} - {isp} - Ping: {ping} ms")
            return (ip, port, country_code, isp, True, ping)
        else:
            print(f"❌ Proxy {ip}:{port} is DEAD")
            return (ip, port, country_code, isp, False, ping)

    except requests.exceptions.RequestException:
        print(f"⏳ Proxy {proxy} is NOT RESPONDING")
        return (ip, port, "Unknown", "Unknown", False, float("inf"))

def check_proxies():
    print("📝 Script started. Mulai memproses proxy...")
    
    if not os.path.exists("proxies.txt"):
        print("File proxies.txt tidak ditemukan!")
        return

    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f.readlines() if line.strip()]

    alive_proxies = []

    for proxy in proxies:
        ip, port, country, isp, is_alive, ping = check_proxy(proxy)
        formatted_proxy = f"{ip},{port},{country},{isp},{ping}"

        if is_alive:
            alive_proxies.append((formatted_proxy, ping))

    # Ambil 200 proxy dengan ping terkecil
    alive_proxies.sort(key=lambda x: x[1])  # Urutkan berdasarkan ping
    alive_proxies = [p[0] for p in alive_proxies[:200]]  # Ambil hanya proxy-nya

    # Simpan hanya 200 proxy terbaik
    with open("alive.txt", "w") as f:
        f.write("\n".join(alive_proxies))

    # Menyusun laporan berdasarkan jumlah proxy yang aktif
    total_proxies = len(proxies)
    total_alive = len(alive_proxies)
    report = f"✅ *Hasil Pengecekan Proxy:*\n" \
             f"🔹 *Total Proxy:* {total_proxies}\n" \
             f"✅ *Alive:* {total_alive}\n" \
             f"📊 *Hanya 200 terbaik dengan ping terkecil yang disimpan!*\n"

    print(report)
    send_telegram_message(report)

if __name__ == "__main__":
    check_proxies()
