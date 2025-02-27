import requests
import os

# Ambil API_URL dari secret
API_URL = os.getenv("API_URL")

if not API_URL:
    raise ValueError("API_URL tidak ditemukan di secret! Pastikan sudah diatur.")

def parse_proxy(proxy):
    """Konversi format proxy ke IP:Port jika masih dalam format CSV"""
    return proxy.replace(",", ":")

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

        print(f"API Response for {proxy}: {data}")  # Debugging

        # Normalisasi status proxy
        status = data.get("proxyStatus", "").lower()
        status = status.replace("✅", "").strip()  # Hapus emoji ✅
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

def check_proxies():
    """Baca `proxies.txt`, cek statusnya, lalu simpan hasilnya."""
    if not os.path.exists("proxies.txt"):
        print("File proxies.txt tidak ditemukan! Pastikan sudah mengumpulkan proxy.")
        return

    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f.readlines() if line.strip()]

    alive_proxies = []
    dead_proxies = []

    for proxy in proxies:
        ip, port, country, isp, is_alive = check_proxy(proxy)
        formatted_proxy = f"{ip}:{port},{country},{isp}"
        if is_alive:
            alive_proxies.append(formatted_proxy)
        else:
            dead_proxies.append(formatted_proxy)

    # Simpan hasilnya ke file
    with open("alive.txt", "w") as f:
        f.write("\n".join(alive_proxies))

    with open("dead.txt", "w") as f:
        f.write("\n".join(dead_proxies))

    print(f"Total Alive: {len(alive_proxies)}, Total Dead: {len(dead_proxies)}")

if __name__ == "__main__":
    check_proxies()
