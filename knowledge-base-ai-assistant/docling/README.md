# Docling Tools

Two Python scripts for building a knowledge base from local documents and web pages:

- **`doc_scraping.py`** — converts documents from the `data/` folder to Markdown using [Docling](https://docling-project.github.io/docling/), then optionally builds a semantic search index.
- **`web_crawl.py`** — crawls a website for pages on the same domain, saves them as HTML files under `data/web/`, then runs `doc_scraping.py ingest`.

## Project layout

```
knowledge-base-ai-assistant/
├── data/                  # Source documents (PDF, DOCX, HTML, etc.)
│   └── web/               # HTML pages saved by web_crawl.py
├── out/                   # Converted Markdown files and search index (created on run)
└── docling/
    ├── doc_scraping.py
    └── web_crawl.py
```

## Requirements

- Python 3.9+

Install dependencies for `doc_scraping.py`:

```bash
pip install typer rich docling sentence-transformers faiss-cpu langchain-text-splitters torch numpy
```

Install additional dependencies for `web_crawl.py`:

```bash
pip install requests beautifulsoup4
```

## doc_scraping.py

Converts Docling-supported files from the `data/` folder to Markdown. Supported formats include PDF, DOCX, PPTX, XLSX, HTML, Markdown, CSV, AsciiDoc, LaTeX, images, and more.

### Convert all documents in `data/`

Place your files under `../data/`, then run:

```bash
cd knowledge-base-ai-assistant/docling
python doc_scraping.py ingest
```

This will:

1. Scan `../data/` recursively for supported files
2. Write `.md` files to `../out/` (preserving subdirectory structure)
3. Build a FAISS search index under `../out/index/`

### Custom input and output folders

```bash
python doc_scraping.py ingest --data-dir ../data --out-dir ../out
```

### Convert without building the search index

```bash
python doc_scraping.py ingest --no-build-index
```

### Search the indexed content

After running `ingest` with indexing enabled:

```bash
python doc_scraping.py query "your search question here"
```

Return more results:

```bash
python doc_scraping.py query "your search question here" --k 10
```

Use a custom index location:

```bash
python doc_scraping.py query "your search question here" --index-dir ../out/index
```

## web_crawl.py

Crawls a website starting from a base URL, saves same-domain pages as HTML under `data/web/`, then runs `doc_scraping.py ingest` to convert everything in `data/`.

### Usage

1. Open `web_crawl.py` and set the target site:

```python
base = "https://example.com"   # change this
urls = crawl(base, max_pages=30)
```

2. Run the crawler:

```bash
cd knowledge-base-ai-assistant/docling
python web_crawl.py
```

The script will:

1. Discover pages on the same domain
2. Save each page as an HTML file under `../data/web/`
3. Run `python doc_scraping.py ingest` to convert all files in `data/`

### Crawl options

Adjust behavior by editing the `crawl()` call in `web_crawl.py`:

- `max_pages` — maximum number of pages to visit (default in `__main__`: 30)
- The `crawl()` function default limit is 50 if called without `max_pages`

## Typical workflows

### Local documents only

1. Copy PDFs, DOCX, HTML, and other files into `../data/`
2. Run `python doc_scraping.py ingest`
3. Read the Markdown output in `../out/`
4. Optionally search with `python doc_scraping.py query "..."`

### Website content

1. Set the base URL in `web_crawl.py`
2. Run `python web_crawl.py` (saves HTML to `data/web/` and runs ingest)
3. Review converted pages in `../out/`
4. Search with `python doc_scraping.py query "..."`

### Local documents + web pages

1. Put local files in `../data/`
2. Run `python web_crawl.py` to add crawled HTML pages under `data/web/`
3. Run `python doc_scraping.py ingest` if you added files manually without using `web_crawl.py`

## Notes

- `doc_scraping.py ingest` only reads files from the `data/` folder; it does not accept URLs or file paths on the command line.
- `doc_scraping.py` uses [Docling](https://docling-project.github.io/docling/) for format detection and conversion; unsupported files are skipped with an error message.
- The FAISS index uses the `sentence-transformers/all-MiniLM-L6-v2` embedding model. The first run may download model weights.
- `web_crawl.py` only follows links on the same domain as the starting URL.
- For production use, consider adding rate limiting, robots.txt checks, and CLI arguments to `web_crawl.py` instead of editing the script directly.
