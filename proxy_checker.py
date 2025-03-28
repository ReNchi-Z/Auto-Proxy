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
        return (proxy, "Unknown", "Unknown", "Unknown", False, 9999.0)

    api_url = API_URL.format(ip=f"{ip}:{port}")

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        status = data.get("proxyStatus", "").lower()
        status = status.replace("✅", "").strip()
        country_code = data.get("countryCode", "Unknown")
        isp = data.get("isp", "Unknown")

        # Perbaikan penanganan delay jika "N/A"
        ping_str = data.get("delay", "9999").replace(" ms", "").strip()
        ping = float(ping_str) if ping_str.replace(".", "").isdigit() else 9999.0

        if "active" in status:
            print(f"✅ Proxy {ip}:{port} is ACTIVE (Ping: {ping} ms)")
            return (ip, port, country_code, isp, True, ping)
        else:
            print(f"❌ Proxy {ip}:{port} is DEAD")
            return (ip, port, country_code, isp, False, ping)

    except requests.exceptions.RequestException:
        print(f"⏳ Proxy {proxy} is NOT RESPONDING")
        return (ip, port, "Unknown", "Unknown", False, 9999.0)

def check_proxies():
    print("📝 Script started. Mulai memproses proxy...")
    
    if not os.path.exists("proxies.txt"):
        print("File proxies.txt tidak ditemukan!")
        return

    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f.readlines() if line.strip()]

    alive_proxies = defaultdict(list)
    dead_proxies = []
    not_responding_proxies = []

    country_stats = defaultdict(lambda: {"alive": 0, "dead": 0, "not_responding": 0})

    for proxy in proxies:
        ip, port, country, isp, is_alive, ping = check_proxy(proxy)
        formatted_proxy = f"{ip},{port},{country},{isp}"

        if is_alive:
            alive_proxies[country].append((formatted_proxy, ping))
            country_stats[country]["alive"] += 1
        else:
            if country == "Unknown" and isp == "Unknown":
                not_responding_proxies.append(f"{ip},{port}")
                country_stats[country]["not_responding"] += 1
            else:
                dead_proxies.append(formatted_proxy)
                country_stats[country]["dead"] += 1

    # Simpan proxy not responding untuk dicek ulang nanti
    with open("not_responding.txt", "w") as f:
        f.write("\n".join(not_responding_proxies))

    # Proses penyimpanan hanya 200 proxy dengan ping terkecil per negara
    with open("alive.txt", "w") as f:
        for country, proxy_list in alive_proxies.items():
            proxy_list.sort(key=lambda x: x[1])  # Urutkan berdasarkan ping (terkecil dulu)
            top_200 = [p[0] for p in proxy_list[:200]]  # Ambil 200 proxy terbaik
            f.write("\n".join(top_200) + "\n")

    with open("dead.txt", "w") as f:
        f.write("\n".join(dead_proxies))

    # Menyusun laporan berdasarkan negara
    total_proxies = len(proxies)
    report = f"✅ *Hasil Pengecekan Proxy:*\n" \
             f"🔹 *Total Proxy:* {total_proxies}\n" \
             f"✅ *Alive:* {sum(len(p) for p in alive_proxies.values())}\n" \
             f"❌ *Dead:* {len(dead_proxies)}\n" \
             f"⏳ *Not Responding:* {len(not_responding_proxies)}\n\n" \
             f"🌍 *Berdasarkan Negara:*\n"

    for country, stats in country_stats.items():
        if country == "Unknown":
            continue  # Lewati jika negara tidak terdeteksi
        flag = country_flag(country)  # Mengubah kode negara menjadi emoji bendera
        report += f"{flag} {country}: {stats['alive']} Alive, {stats['dead']} Dead, {stats['not_responding']} Not Responding\n"

    print(report)
    send_telegram_message(report)

if __name__ == "__main__":
    check_proxies()
