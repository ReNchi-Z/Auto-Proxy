import os
import requests
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ambil variabel dari Secret dan filter agar tidak ada URL kosong
PROXY_SOURCES = [url.strip() for url in os.getenv("PROXY_SOURCES", "").split(",") if url.strip()]
API_URL = os.getenv('API_URL', 'https://api.renchi.workers.dev/api?ip={ip}')

# File output
ALIVE_FILE = "alive.txt"
DEAD_FILE = "dead.txt"

def fetch_proxies(url):
    """Mengambil daftar proxy dari URL dan mengembalikan set unik."""
    if not url:
        print("Skipping empty URL")
        return set()
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return {line.strip() for line in response.text.splitlines() if line.strip()}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return set()

def collect_proxies():
    """Mengumpulkan proxy dari berbagai sumber dan menghapus duplikasi."""
    all_proxies = set()
    for url in PROXY_SOURCES:
        all_proxies.update(fetch_proxies(url))
    
    print(f"Total proxies collected: {len(all_proxies)}")
    return all_proxies

def parse_proxy(proxy):
    """Mengambil hanya IP dan Port dari format IP,Port,Country,ISP jika diperlukan."""
    parts = proxy.split(",")  # Jika data terpisah dengan koma
    if len(parts) >= 2:  # Pastikan ada setidaknya IP dan Port
        ip = parts[0].strip()
        port = parts[1].strip()
        return f"{ip}:{port}"
    return proxy  # Jika sudah dalam format IP:Port, langsung dikembalikan

def check_proxy(proxy):
    """Cek apakah proxy aktif atau tidak."""
    proxy = parse_proxy(proxy)  # Pastikan formatnya IP:Port
    try:
        ip, port = proxy.split(":")
    except ValueError:
        print(f"Invalid proxy format: {proxy}")
        return (proxy, "Unknown", "Unknown", "Unknown", False)

    api_url = API_URL.format(ip=f"{ip}:{port}")

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        status = data.get("proxyStatus", "").strip().lower()
        country_code = data.get("countryCode", "Unknown")
        isp = data.get("isp", "Unknown")

        if "active" in status:
            print(f"{ip}:{port} is ALIVE")
            return (ip, port, country_code, isp, True)
        else:
            print(f"{ip}:{port} is DEAD")
            return (ip, port, country_code, isp, False)

    except requests.exceptions.RequestException as e:
        print(f"Error checking {ip}:{port}: {e}")
        return (ip, port, "Unknown", "Unknown", False)

def main():
    """Jalankan pengumpulan dan pengecekan proxy."""
    proxies = collect_proxies()
    alive_proxies = []
    dead_proxies = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_proxy, proxy): proxy for proxy in proxies}

        for future in as_completed(futures):
            ip, port, country_code, isp, is_alive = future.result()
            if is_alive:
                alive_proxies.append((ip, port, country_code, isp))
            else:
                dead_proxies.append((ip, port, country_code, isp))

    # Simpan hasil ke file
    with open(ALIVE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IP", "Port", "Country Code", "ISP"])
        writer.writerows(alive_proxies)

    with open(DEAD_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IP", "Port", "Country Code", "ISP"])
        writer.writerows(dead_proxies)

if __name__ == "__main__":
    main()
