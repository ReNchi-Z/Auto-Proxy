import os
import requests
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ambil API URL dari Secrets
api_url_template = os.getenv("API_URL", "https://api.renchi.workers.dev/api?ip={ip}")

input_file = "input_file.txt"
alive_file = "alive.txt"
dead_file = "dead.txt"
error_file = "error.txt"

def check_proxy(row):
    ip, port = row[0].strip(), row[1].strip()
    api_url = api_url_template.format(ip=f"{ip}:{port}")

    try:
        response = requests.get(api_url, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Ambil data dari API
        proxy_host = data.get("proxyHost", "Unknown")
        proxy_port = data.get("proxyPort", "Unknown")
        isp = data.get("isp", "Unknown")
        country_code = data.get("countryCode", "Unknown")
        proxy_status = data.get("proxyStatus", "").strip().lower()

        if "active" in proxy_status.lower():
            print(f"{proxy_host}:{proxy_port} is ALIVE")
            with open(alive_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([proxy_host, proxy_port, country_code, isp])  # Format hasil aktif
        else:
            print(f"{proxy_host}:{proxy_port} is DEAD")
            with open(dead_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([proxy_host, proxy_port])

    except requests.exceptions.RequestException as e:
        with open(error_file, "a") as f:
            f.write(f"Error checking {ip}:{port}: {e}\n")
    except ValueError as ve:
        with open(error_file, "a") as f:
            f.write(f"JSON Error for {ip}:{port}: {ve}\n")
            f.write(f"Response received: {response.text}\n")

# Bersihkan hasil lama sebelum scan baru
for file in [alive_file, dead_file, error_file]:
    open(file, "w").close()

# Baca proxy dari file
with open(input_file, "r") as f:
    reader = csv.reader(f)
    rows = [row for row in reader if len(row) >= 2]

# Scan proxy dengan multi-threading (50 worker)
with ThreadPoolExecutor(max_workers=50) as executor:
    executor.map(check_proxy, rows)
