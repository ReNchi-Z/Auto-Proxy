import os
import requests

# Ambil daftar sumber dari Secrets
proxy_sources = os.getenv("PROXY_SOURCES", "").split(",")

proxies = set()  # Gunakan set untuk menghindari duplikasi

for url in proxy_sources:
    url = url.strip()
    if not url:
        continue  # Lewati jika URL kosong

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Cek jika URL tidak valid
        
        lines = response.text.strip().split("\n")
        for line in lines:
            parts = line.strip().split(",")  # Pisahkan berdasarkan koma
            if len(parts) >= 2:  # Pastikan ada setidaknya IP dan Port
                ip_port = f"{parts[0]}:{parts[1]}"  # Ambil IP dan Port saja
                proxies.add(ip_port)

    except requests.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")  # Log error tapi tetap lanjut

# Simpan hasil ke file
with open("proxies.txt", "w") as f:
    f.write("\n".join(proxies))

print(f"✅ Total proxies collected: {len(proxies)}")
