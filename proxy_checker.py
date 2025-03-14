import requests
import os
from collections import defaultdict
import time

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

def check_proxy(proxy, retry=False):
    """Mengecek status proxy, jika tidak merespon akan dicek ulang sekali lagi."""
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

        status = data.get("proxyStatus", "").lower()
        status = status.replace("✅", "").strip()
        country_code = data.get("countryCode", "Unknown")
        isp = data.get("isp", "Unknown")
        ping = float(data.get("delay", "9999").replace(" ms", "").strip())

        if "active" in status:
            print(f"✅ Proxy {ip}:{port} is ACTIVE (Ping: {ping} ms)")
            return (ip, port, country_code, isp, True, ping)
        else:
            print(f"❌ Proxy {ip}:{port} is DEAD")
            return (ip, port, country_code, isp, False, ping)

    except requests.exceptions.RequestException:
        if not retry:
            print(f"⏳ Proxy {proxy} is NOT RESPONDING, mencoba lagi...")
            time.sleep(3)  # Tunggu sebentar sebelum pengecekan ulang
            return check_proxy(proxy, retry=True)
        else:
            print(f"⏳ Proxy {proxy} tetap NOT RESPONDING setelah pengecekan ulang")
            return (ip, port, "Unknown", "Unknown", False, float("inf"))

def check_proxies():
    print("📝 Script started. Mulai memproses proxy...")
    
    if not os.path.exists("proxies.txt"):
        print("File proxies.txt tidak ditemukan!")
        return

    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f.readlines() if line.strip()]

    alive_proxies = defaultdict(list)
    not_responding_proxies = []

    for proxy in proxies:
        ip, port, country, isp, is_alive, ping = check_proxy(proxy)
        formatted_proxy = f"{ip},{port},{country},{isp}"

        if is_alive:
            alive_proxies[country].append((formatted_proxy, ping))
        elif ping == float("inf"):  # Proxy yang tetap tidak merespon setelah dicek ulang
            not_responding_proxies.append(f"{ip},{port}")  # Hanya simpan IP & Port

    # Simpan hanya 200 proxy terbaik per negara
    with open("alive.txt", "w") as f:
        for country, proxy_list in alive_proxies.items():
            proxy_list.sort(key=lambda x: x[1])  # Urutkan berdasarkan ping
            top_200 = [p[0] for p in proxy_list[:200]]  # Ambil 200 terbaik
            f.write("\n".join(top_200) + "\n")

    # Simpan hanya IP dan Port dari proxy yang tetap tidak merespon
    with open("not_responding.txt", "w") as f:
        f.write("\n".join(not_responding_proxies))

    # Hitung jumlah proxy aktif per negara
    report = f"✅ *Hasil Pengecekan Proxy:*\n" \
             f"🔹 *Total Proxy Dicek:* {len(proxies)}\n" \
             f"✅ *Total Proxy Aktif:* {sum(len(p) for p in alive_proxies.values())}\n" \
             f"📊 *200 terbaik disimpan per negara!*\n\n" \
             f"🌍 *Berdasarkan Negara:*\n"

    for country, proxy_list in alive_proxies.items():
        flag = country_flag(country)
        report += f"{flag} {country}: {len(proxy_list)} aktif\n"

    print(report)
    send_telegram_message(report)

if __name__ == "__main__":
    check_proxies()
