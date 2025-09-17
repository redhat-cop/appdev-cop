from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

import typer
from rich import print
from langchain_text_splitters import RecursiveCharacterTextSplitter

from docling.document_converter import DocumentConverter
# Docling supports PDF, DOCX, PPTX, XLSX, HTML, Markdown and more via one API.  :contentReference[oaicite:4]{index=4}

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

app = typer.Typer()

def convert_to_markdown(inputs: List[str], out_dir: Path) -> List[Dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    conv = DocumentConverter()
    results = []

    for src in inputs:
        res = conv.convert(src)
        md = res.document.export_to_markdown()  # unified Markdown export  :contentReference[oaicite:5]{index=5}
        base = Path(res.input.file.stem if res.input.file else "doc")
        md_path = out_dir / f"{base}.md"
        md_path.write_text(md, encoding="utf-8")

        # keep structured JSON too (useful later)
        j = res.document.export_to_dict()
        (out_dir / f"{base}.json").write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")

        results.append({"source": str(src), "md_path": str(md_path)})
        print(f"[green]✓[/green] Converted: {src} → {md_path}")
    return results

def chunk_markdown(md_text: str, chunk_size=1200, overlap=200) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n## ", "\n### ", "\n", " ", ""],  # prefer heading-aware splits
    )
    return splitter.split_text(md_text)

def build_faiss_index(md_files: List[Path], meta: List[Dict[str, Any]], index_dir: Path, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    index_dir.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(model_name)
    texts, metadatas = [], []

    for rec in meta:
        md_path = Path(rec["md_path"])
        text = md_path.read_text(encoding="utf-8")
        chunks = chunk_markdown(text)
        for i, c in enumerate(chunks):
            texts.append(c)
            metadatas.append({
                "source": rec["source"],
                "file": str(md_path),
                "chunk_id": i
            })

    # embed
    embs = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    # normalize for cosine similarity on dot product
    faiss.normalize_L2(embs)
    index.add(embs)

    # persist
    faiss.write_index(index, str(index_dir / "index.faiss"))
    (index_dir / "texts.json").write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
    (index_dir / "metadatas.json").write_text(json.dumps(metadatas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[blue]FAISS index built[/blue]: {len(texts)} chunks")

def search(index_dir: Path, query: str, top_k=5, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    index = faiss.read_index(str(index_dir / "index.faiss"))
    texts = json.loads((index_dir / "texts.json").read_text(encoding="utf-8"))
    metadatas = json.loads((index_dir / "metadatas.json").read_text(encoding="utf-8"))

    model = SentenceTransformer(model_name)
    q = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q)
    D, I = index.search(q, top_k)

    results = []
    for score, idx in zip(D[0], I[0]):
        if idx == -1:
            continue
        results.append({
            "score": float(score),
            "text": texts[idx],
            "meta": metadatas[idx]
        })
    return results

@app.command()
def ingest(
    inputs: List[str] = typer.Argument(..., help="Files or URLs: HTML/wiki, README.md, PDF, DOCX, etc."),
    out_dir: Path = typer.Option("artifacts", help="Where to store .md/.json and index"),
    build_index: bool = typer.Option(True, help="Build FAISS index after ingest")
):
    out_md = out_dir / "markdown"
    meta = convert_to_markdown(inputs, out_md)
    if build_index:
        build_faiss_index([Path(m["md_path"]) for m in meta], meta, out_dir / "index")

@app.command()
def query(
    q: str = typer.Argument(..., help="Search query"),
    index_dir: Path = typer.Option("artifacts/index", help="Index directory"),
    k: int = typer.Option(5, help="Top-K")
):
    hits = search(index_dir, q, k)
    for h in hits:
        print(f"\n[bold]{h['meta']['source']}[/bold]  (score={h['score']:.3f}, chunk={h['meta']['chunk_id']})\n{h['text'][:600]}")

if __name__ == "__main__":
    app()
