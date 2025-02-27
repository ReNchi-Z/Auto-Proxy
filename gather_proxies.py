import os
import requests

# Ambil daftar sumber proxy dari GitHub Secrets (dipisahkan dengan koma)
proxy_sources = os.getenv("PROXY_SOURCES", "").split(",")

output_file = "input_file.txt"
proxy_set = set()  # Menggunakan set agar duplikat otomatis dihapus

for source in proxy_sources:
    source = source.strip()
    if not source:
        continue
    try:
        response = requests.get(source, timeout=30)
        response.raise_for_status()
        lines = response.text.splitlines()

        for line in lines:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                ip, port = parts[0].strip(), parts[1].strip()
                proxy_set.add(f"{ip},{port}")  # Simpan dalam set untuk menghapus duplikat

    except requests.RequestException as e:
        print(f"Error fetching {source}: {e}")

# Simpan hasil unik ke file input_file.txt
with open(output_file, "w") as f:
    for proxy in sorted(proxy_set):  # Sort agar lebih rapi
        f.write(proxy + "\n")

print(f"Total unique proxies collected: {len(proxy_set)}")
