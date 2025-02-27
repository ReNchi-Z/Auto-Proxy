import requests
import os

API_URL = os.getenv("API_URL")

if not API_URL:
    raise ValueError("API_URL tidak ditemukan di secret! Pastikan sudah diatur.")

def parse_proxy(proxy):
    return proxy.replace(",", ":")

def check_proxy(proxy):
    proxy = parse_proxy(proxy)
    try:
        ip, port = proxy.split(":")
    except ValueError:
        print(f"❌ Proxy format tidak valid: {proxy}")
        return (proxy, "Unknown", "Unknown", "Unknown", False)

    api_url = API_URL.format(ip=f"{ip}:{port}")

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        status = data.get("proxyStatus", "").lower()
        status = status.replace("✅", "").strip()
        country_code = data.get("countryCode", "Unknown")
        isp = data.get("isp", "Unknown")

        if "active" in status:
            print(f"✅ Proxy {ip}:{port} is ACTIVE")
            return (ip, port, country_code, isp, True)
        else:
            print(f"❌ Proxy {ip}:{port} is DEAD")
            return (ip, port, country_code, isp, False)

    except requests.exceptions.RequestException:
        # Tidak perlu menyertakan detail API URL atau error lainnya
        print(f"⏳ Proxy {proxy} is NOT RESPONDING")
        return (ip, port, "Unknown", "Unknown", False)

def check_proxies():
    if not os.path.exists("proxies.txt"):
        print("File proxies.txt tidak ditemukan!")  # Log jika file tidak ditemukan
        return

    with open("proxies.txt", "r") as f:
        proxies = [line.strip() for line in f.readlines() if line.strip()]

    alive_proxies = []
    dead_proxies = []
    not_responding_proxies = []

    for proxy in proxies:
        ip, port, country, isp, is_alive = check_proxy(proxy)
        formatted_proxy = f"{ip}:{port},{country},{isp}"
        if is_alive:
            alive_proxies.append(formatted_proxy)
        else:
            if country == "Unknown" and isp == "Unknown":
                not_responding_proxies.append(formatted_proxy)
            else:
                dead_proxies.append(formatted_proxy)

    with open("alive.txt", "w") as f:
        f.write("\n".join(alive_proxies))

    with open("dead.txt", "w") as f:
        f.write("\n".join(dead_proxies))

    with open("not_responding.txt", "w") as f:
        f.write("\n".join(not_responding_proxies))

    print(f"✅ Total Alive: {len(alive_proxies)} | ❌ Total Dead: {len(dead_proxies)} | ⏳ Total Not Responding: {len(not_responding_proxies)}")

if __name__ == "__main__":
    check_proxies()
