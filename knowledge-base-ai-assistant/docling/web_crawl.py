import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

visited = set()
to_visit = []

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data"


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


def url_to_filename(url: str) -> str:
    parsed = urlparse(url)
    path_part = parsed.path.strip("/").replace("/", "_") or "index"
    safe_path = re.sub(r"[^\w.-]", "_", path_part)
    return f"{parsed.netloc}_{safe_path}.html"


def save_pages(urls, data_dir=DEFAULT_DATA_DIR):
    data_dir = Path(data_dir)
    crawl_dir = data_dir / "web"
    crawl_dir.mkdir(parents=True, exist_ok=True)

    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            page_path = crawl_dir / url_to_filename(url)
            page_path.write_text(response.text, encoding="utf-8")
            print(f"Saved: {url} → {page_path}")
        except Exception as e:
            print(f"Error saving {url}: {e}")


if __name__ == "__main__":
    base = "https://example.com"   # change this
    urls = crawl(base, max_pages=30)
    save_pages(urls)

    cmd = ["python", "doc_scraping.py", "ingest"]
    subprocess.run(cmd)
