import requests
import os

# Ambil daftar sumber proxy dari secret
PROXY_SOURCES = os.getenv("PROXY_SOURCES")

if not PROXY_SOURCES:
    raise ValueError("PROXY_SOURCES tidak ditemukan di secret!")

def fetch_proxies():
    """Mengambil daftar proxy dari beberapa sumber dan menyimpannya ke file."""
    sources = PROXY_SOURCES.split("\n")
    proxies = []

    for url in sources:
        url = url.strip()
        if not url:
            continue

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            new_proxies = response.text.strip().split("\n")
            proxies.extend(new_proxies)
            print(f"Fetched {len(new_proxies)} proxies from {url}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")

    # Simpan semua proxy yang dikumpulkan ke file
    with open("proxies.txt", "w") as f:
        f.write("\n".join(proxies))

    print(f"Total proxies collected: {len(proxies)}")

if __name__ == "__main__":
    fetch_proxies()
