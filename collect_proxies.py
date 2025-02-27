import os
import requests

proxy_sources = os.getenv("PROXY_SOURCES", "").split(",")
proxies = set()
asia_countries = {
    "CN", "IN", "JP", "KR", "SG", "ID", "MY", "TH", "VN", "PH", "PK", "BD", 
    "NP", "LK", "MN", "MM", "KH", "LA", "TL", "KW", "QA", "AE", "SA", "OM", 
    "JO", "SY", "LB", "IQ", "KW", "BH", "YE", "AE", "SG", "ID"
}

for url in proxy_sources:
    url = url.strip()
    if not url:
        continue

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        lines = response.text.strip().split("\n")
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) >= 4:
                ip = parts[0]
                port = parts[1]
                countryid = parts[2]
                
                if countryid in asia_countries:
                    ip_port = f"{ip}:{port}"
                    proxies.add(ip_port)

    except requests.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")

with open("proxies.txt", "w") as f:
    f.write("\n".join(proxies))

print(f"✅ Total proxies collected: {len(proxies)}")
