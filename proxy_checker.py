import requests
import os
from collections import defaultdict

API_URL = os.getenv("API_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not API_URL:
    raise ValueError("API_URL tidak ditemukan di secret! Pastikan sudah diatur.")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("📩 Notifikasi terkirim ke Telegram!")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Gagal mengirim notifikasi Telegram: {e}")

def country_flag(iso_code):
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

        status = data.get("proxyStatus", "").lower()
        status = status.replace("✅", "").strip()
        country_code = data.get("countryCode", "Unknown")
        isp = data.get("isp", "Unknown")
        ping = float(data.get("ping", 9999))

        if "active" in status:
            print(f"✅ Proxy {ip}:{port} is ACTIVE (Ping: {ping} ms)")
            return (ip, port, country_code, isp, True, ping)
        else:
            print(f"❌ Proxy {ip}:{port} is DEAD")
            return (ip, port, country_code, isp, False, float("inf"))

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
    dead_proxies = []
    not_responding_proxies = []

    country_stats = defaultdict(lambda: {"alive": 0, "dead": 0, "not_responding": 0})

    for proxy in proxies:
        ip, port, country, isp, is_alive, ping = check_proxy(proxy)
        print(f"🔍 {ip}:{port} - {country} - {isp} - Ping: {ping} ms")

        formatted_proxy = f"{ip},{port},{country},{isp}"

        if is_alive:
            alive_proxies.append((formatted_proxy, ping))
            country_stats[country]["alive"] += 1
        else:
            if country == "Unknown" and isp == "Unknown":
                not_responding_proxies.append(formatted_proxy)
                country_stats[country]["not_responding"] += 1
            else:
                dead_proxies.append(formatted_proxy)
                country_stats[country]["dead"] += 1

    alive_proxies.sort(key=lambda x: x[1])
    alive_proxies = [x[0] for x in alive_proxies[:200]]

    with open("alive.txt", "w") as f:
        f.write("\n".join(alive_proxies))

    with open("dead.txt", "w") as f:
        f.write("\n".join(dead_proxies))

    with open("not_responding.txt", "w") as f:
        f.write("\n".join(not_responding_proxies))

    total_proxies = len(alive_proxies) + len(dead_proxies) + len(not_responding_proxies)
    report = f"✅ *Hasil Pengecekan Proxy:*\n" \
             f"🔹 *Total Proxy:* {total_proxies}\n" \
             f"✅ *Alive (Top 200 by Ping):* {len(alive_proxies)}\n" \
             f"❌ *Dead:* {len(dead_proxies)}\n" \
             f"⏳ *Not Responding:* {len(not_responding_proxies)}\n\n" \
             f"🌍 *Berdasarkan Negara:*\n"

    for country, stats in country_stats.items():
        if country == "Unknown":
            continue
        flag = country_flag(country)
        report += f"{flag} {country}: {stats['alive']} Alive, {stats['dead']} Dead, {stats['not_responding']} Not Responding\n"

    print(report)
    send_telegram_message(report)

if __name__ == "__main__":
    check_proxies()
