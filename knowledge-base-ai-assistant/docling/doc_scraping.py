from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import faiss
import typer
from docling.datamodel.base_models import FormatToExtensions
from docling.document_converter import DocumentConverter
# Docling supports PDF, DOCX, PPTX, XLSX, HTML, Markdown and more via one API.
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich import print
from sentence_transformers import SentenceTransformer

app = typer.Typer()

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data"
DEFAULT_OUT_DIR = SCRIPT_DIR.parent / "out"

SUPPORTED_EXTENSIONS = {
    ext.lower()
    for extensions in FormatToExtensions.values()
    for ext in extensions
}


# Return True when a file extension is supported by Docling.
def is_supported_document(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith(".tar.gz"):
        return True
    return path.suffix.lstrip(".").lower() in SUPPORTED_EXTENSIONS


# Recursively collect all Docling-supported documents under data_dir.
def collect_documents(data_dir: Path) -> List[Path]:
    if not data_dir.is_dir():
        raise typer.BadParameter(f"Data directory not found: {data_dir}")

    documents = [
        path
        for path in sorted(data_dir.rglob("*"))
        if path.is_file() and is_supported_document(path)
    ]

    if not documents:
        print(f"[yellow]No supported documents found in {data_dir}[/yellow]")

    return documents


# Build the output Markdown path, preserving relative layout from data_dir.
def resolve_output_path(
    src: Path,
    out_dir: Path,
    data_dir: Path,
    converted_stem: str,
) -> Path:
    relative = src.relative_to(data_dir)
    return out_dir / relative.with_suffix(".md")


# Convert local files to Markdown using Docling and write them to out_dir.
def convert_to_markdown(
    inputs: List[Path],
    out_dir: Path,
    data_dir: Path,
) -> List[Dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    conv = DocumentConverter()
    results = []

    for src in inputs:
        src_display = str(src)
        try:
            res = conv.convert(src_display)
            md = res.document.export_to_markdown()  # unified Markdown export
            base = Path(res.input.file.stem if res.input.file else src.stem)
            md_path = resolve_output_path(src, out_dir, data_dir, base)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md, encoding="utf-8")

            results.append({"source": src_display, "md_path": str(md_path)})
            print(f"[green]✓[/green] Converted: {src_display} → {md_path}")
        except Exception as exc:
            print(f"[red]✗[/red] Failed: {src_display} ({exc})")

    return results


# Split Markdown into overlapping chunks for embedding and search.
def chunk_markdown(md_text: str, chunk_size=1200, overlap=200) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n## ", "\n### ", "\n", " ", ""],  # prefer heading-aware splits
    )
    return splitter.split_text(md_text)


# Embed Markdown chunks and persist a FAISS index for semantic search.
def build_faiss_index(
    meta: List[Dict[str, Any]],
    index_dir: Path,
    model_name="sentence-transformers/all-MiniLM-L6-v2",
):
    index_dir.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(model_name)
    texts, metadatas = [], []

    for rec in meta:
        md_path = Path(rec["md_path"])
        text = md_path.read_text(encoding="utf-8")
        chunks = chunk_markdown(text)
        for i, chunk in enumerate(chunks):
            texts.append(chunk)
            metadatas.append(
                {
                    "source": rec["source"],
                    "file": str(md_path),
                    "chunk_id": i,
                }
            )

    # embed
    embs = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    # normalize for cosine similarity on dot product
    faiss.normalize_L2(embs)
    index.add(embs)

    # persist
    faiss.write_index(index, str(index_dir / "index.faiss"))
    (index_dir / "texts.json").write_text(
        json.dumps(texts, ensure_ascii=False), encoding="utf-8"
    )
    (index_dir / "metadatas.json").write_text(
        json.dumps(metadatas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[blue]FAISS index built[/blue]: {len(texts)} chunks")


# Search the FAISS index and return the top matching text chunks.
def search(
    index_dir: Path,
    query: str,
    top_k=5,
    model_name="sentence-transformers/all-MiniLM-L6-v2",
):
    index = faiss.read_index(str(index_dir / "index.faiss"))
    texts = json.loads((index_dir / "texts.json").read_text(encoding="utf-8"))
    metadatas = json.loads((index_dir / "metadatas.json").read_text(encoding="utf-8"))

    model = SentenceTransformer(model_name)
    q = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q)
    scores, indices = index.search(q, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        results.append(
            {
                "score": float(score),
                "text": texts[idx],
                "meta": metadatas[idx],
            }
        )
    return results


# CLI command: convert documents from data_dir and optionally build the index.
@app.command()
def ingest(
    data_dir: Path = typer.Option(
        DEFAULT_DATA_DIR,
        help="Folder containing documents to convert",
    ),
    out_dir: Path = typer.Option(
        DEFAULT_OUT_DIR,
        help="Folder where converted Markdown files are written",
    ),
    build_index: bool = typer.Option(
        True,
        help="Build FAISS index after conversion",
    ),
):
    sources = collect_documents(data_dir)

    if not sources:
        raise typer.Exit(code=1)

    print(f"[blue]Converting {len(sources)} document(s) from {data_dir} → {out_dir}[/blue]")
    meta = convert_to_markdown(sources, out_dir, data_dir)

    if not meta:
        raise typer.Exit(code=1)

    if build_index:
        build_faiss_index(meta, out_dir / "index")


# CLI command: run a semantic search query against the built FAISS index.
@app.command()
def query(
    q: str = typer.Argument(..., help="Search query"),
    index_dir: Path = typer.Option(
        DEFAULT_OUT_DIR / "index",
        help="Index directory",
    ),
    k: int = typer.Option(5, help="Top-K"),
):
    hits = search(index_dir, q, k)
    for hit in hits:
        print(
            f"\n[bold]{hit['meta']['source']}[/bold]  "
            f"(score={hit['score']:.3f}, chunk={hit['meta']['chunk_id']})\n"
            f"{hit['text'][:600]}"
        )


if __name__ == "__main__":
    app()
