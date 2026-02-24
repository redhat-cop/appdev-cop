import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import subprocess

visited = set()
to_visit = []

def crawl(base_url, max_pages=50):
    domain = urlparse(base_url).netloc
    to_visit.append(base_url)

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)

        if url in visited:
            continue

        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")

            visited.add(url)
            print("Found:", url)

            for link in soup.find_all("a", href=True):
                full_url = urljoin(base_url, link["href"])
                parsed = urlparse(full_url)

                if parsed.netloc == domain:
                    if full_url not in visited:
                        to_visit.append(full_url)

        except Exception as e:
            print("Error:", e)

    return list(visited)


if __name__ == "__main__":
    base = "https://example.com"   # change this
    urls = crawl(base, max_pages=30)

    cmd = ["python", "pipeline.py", "ingest"] + urls
    subprocess.run(cmd)