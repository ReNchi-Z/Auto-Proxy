import os
import requests
import sys

sys.stderr = open(os.devnull, "w")

proxy_sources = os.getenv("PROXY_SOURCES", "").split(",")
proxies = set()

asia_countries = {
    "CN", "IN", "JP", "KR", "SG", "ID", "MY", "TH", "VN", "PH", "PK", "BD", 
    "NP", "LK", "MN", "MM", "KH", "LA", "TL", "KW", "QA", "AE", "SA", "OM", 
    "JO", "SY", "LB", "IQ", "BH", "YE"
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
                ip, port, countryid = parts[:3]
                
                if countryid in asia_countries:
                    ip_port = f"{ip}:{port}"
                    proxies.add(ip_port)

    except requests.RequestException:
        pass

with open("proxies.txt", "w") as f:
    f.write("\n".join(proxies))

print(f"✅ Total proxies collected: {len(proxies)}")
