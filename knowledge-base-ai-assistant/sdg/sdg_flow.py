import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd
from sdg_hub import Flow, FlowRegistry


def require_model_server(api_base: str, model_name: str) -> None:
    """Stop before generation when the local vLLM server is down or serving another model."""
    served_name = model_name.removeprefix("hosted_vllm/")
    models_url = api_base.rstrip("/") + "/models"
    request = urllib.request.Request(models_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:
        raise SystemExit(
            "Model has not started.\n"
            "Start the model, wait until it is ready, then run this Python file again:\n"
            "  python sdg_flow.py\n"
            "\n"
            "Start command:\n"
            "  pkill -f vllm\n"
            "  export VLLM_USE_FLASHINFER_SAMPLER=0\n"
            "  python -m vllm.entrypoints.openai.api_server \\\n"
            f"    --model {served_name} --dtype bfloat16 \\\n"
            "    --gpu-memory-utilization 0.85 \\\n"
            "    --max-model-len 4096 --port 8000 --host 127.0.0.1\n"
            f"Details: {exc}"
        ) from exc

    served_ids = [item.get("id") for item in payload.get("data", [])]
    if served_name not in served_ids:
        raise SystemExit(
            "Model has not started.\n"
            f"A server is running at {api_base}, but {served_name} is not loaded.\n"
            "Start the model, wait until it is ready, then run this Python file again:\n"
            "  python sdg_flow.py\n"
            f"Served models: {served_ids or 'none'}"
        )
    print(f"vLLM is ready at {api_base} with model {served_name}")


# ==============================================================================
# Configuration
# ==============================================================================
# model_name = "hosted_vllm/ibm-granite/granite-3.0-8b-instruct"
model_name = "hosted_vllm/ibm-granite/granite-4.2-8b"
api_base = "http://127.0.0.1:8000/v1"
api_key = "rhoai-local-token"
# api_key = os.getenv("VLLM_API_KEY", "EMPTY")
target_flow = "stellar-peak-605"  # Document Based Knowledge Tuning

try:
    SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    SCRIPT_DIR = Path.cwd()

# The sample uses Path("docling_out") next to the script.
# Docling writes one folder up, in docling/docling_out.
# DOCLING_MD_DIR = Path("docling_out")
DOCLING_MD_DIR = SCRIPT_DIR.parent / "docling" / "docling_out"
# RAW_OUTPUT_PATH = Path("sdg_out/stellar_peak_raw.jsonl")
# TRAIN_READY_JSONL = Path("sdg_out/training_dataset.jsonl")
RAW_OUTPUT_PATH = SCRIPT_DIR / "sdg_out" / "stellar_peak_raw.jsonl"
TRAIN_OUTPUT_PATH = SCRIPT_DIR / "sdg_out" / "synthetic_training_data.jsonl"

# icl_document = "RedHat OpenShift AI 3.5"
ICL_REFERENCE_DOC = (
    "Red Hat OpenShift AI is an artificial intelligence platform that provides tools to rapidly "
    "train, serve, and monitor machine learning models across on-premise, cloud, or disconnected "
    "environments."
)

# 4. Ingest the clean Markdown text created by Docling
# context_file = "/opt/app-root/src/appdev-cop/knowledge-base-ai-assistant/out/RHOAI.md"
# if not os.path.exists(context_file):
#     raise FileNotFoundError(f"Missing context asset: {context_file}. Run Docling first!")
#
# with open(context_file, "r", encoding="utf-8") as f:
#     context_text = f.read()
#
# =====================================================================
# FIX: Chunk text into multiple sections to generate a multi-row dataset
# =====================================================================
# chunk_size = 2500
# chunks = [context_text[i:i+chunk_size] for i in range(0, len(context_text), chunk_size)]
# chunks = chunks[:5]  # Cap at 5 rows to keep your live demo execution fast
#
# print(f"🧩 Split document into {len(chunks)} distinct segments for generation...")


def is_table_of_contents(heading: str) -> bool:
    normalized = re.sub(r"[^a-z]+", " ", heading.lower()).strip()
    return normalized in {"table of contents", "contents", "toc"} or normalized.startswith(
        "table of contents"
    )


def extract_markdown_sections(md_dir: Path, min_chars: int = 100) -> list[tuple[str, str, str]]:
    """Read Markdown files and split them into sections based on headings."""
    if not md_dir.is_dir():
        raise FileNotFoundError(
            f"No .md files found in {md_dir}. Please place your Docling output here."
        )

    md_files = sorted(path for path in md_dir.rglob("*.md") if path.is_file())
    if not md_files:
        raise FileNotFoundError(
            f"No .md files found in {md_dir}. Please place your Docling output here."
        )

    # heading_pattern = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    heading_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    sections = []

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8").strip()
        matches = list(heading_pattern.finditer(text))

        # If no headings exist, treat the whole document as one section
        if not matches and len(text) >= min_chars:
            sections.append((md_file.name, md_file.stem, text))
            continue

        # Extract content under each heading. The heading itself is document_outline.
        for idx, match in enumerate(matches):
            heading = match.group(2).strip()
            if is_table_of_contents(heading):
                continue
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()
            if len(section_text) >= min_chars:
                sections.append((md_file.name, heading, section_text))

    return sections


def run_sdg_flow(sections: list[tuple[str, str, str]], max_concurrency: int = 8) -> pd.DataFrame:
    """Run stellar-peak-605 on Docling sections and write the raw and training files."""
    raw_data = []
    for _source_name, heading, section_text in sections:
        raw_data.append({
            "document": section_text,
            # "document_outline": "Red Hat OpenShift AI Self-Managed Getting Started Guide.",
            "document_outline": heading,
            "domain": "Enterprise AI",
            "icl_document": "RHOAI 3.5",
            "icl_query_1": "What are the core steps in the OpenShift AI workflow?",
            "icl_query_2": "How do I set up a project and workbench?",
            "icl_query_3": "Explain the difference between model serving and AI pipelines.",
            "icl_query_4": "How do connections help with Object Storage?",
            "icl_query_5": "How do workbenches help with model development and training?",
        })

    input_df = pd.DataFrame(raw_data)
    print(f"Prepared {len(input_df)} document sections for generation.")

    FlowRegistry.discover_flows()
    # flow_path = FlowRegistry.get_flow_path(target_flow) or FlowRegistry.get_flow_path("Document Based Knowledge Tuning")
    flow_path = FlowRegistry.get_flow_path_safe(target_flow) or FlowRegistry.get_flow_path_safe(
        "Document Based Knowledge Tuning"
    )
    if not flow_path:
        raise ValueError(f"Flow '{target_flow}' not found in FlowRegistry.")

    flow = Flow.from_yaml(flow_path)
    # The answer step in stellar-peak-605 asks for 4096 tokens.
    # This vLLM server allows 4096 tokens total, so that request leaves no room for the prompt.
    flow.set_model_config(
        model=model_name,
        api_base=api_base,
        api_key=api_key,
        max_tokens=1024,
    )

    print(f"Generating question-answer pairs with '{target_flow}'...")
    result_df = flow.generate(input_df, max_concurrency=max_concurrency)

    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_json(RAW_OUTPUT_PATH, orient="records", lines=True, force_ascii=False)
    print(f"Saved {len(result_df)} raw rows -> {RAW_OUTPUT_PATH}")

    exported = 0
    with TRAIN_OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for _, row in result_df.iterrows():
            question = row.get("question") or row.get("query")
            answer = row.get("response") or row.get("answer")
            if pd.notna(question) and pd.notna(answer) and str(question).strip() and str(answer).strip():
                record = {
                    "messages": [
                        {"role": "user", "content": str(question).strip()},
                        {"role": "assistant", "content": str(answer).strip()},
                    ]
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                exported += 1

    print(f"Success! Exported {exported} training pairs to {TRAIN_OUTPUT_PATH}")
    return result_df


def main() -> None:
    print("=========================================================")
    print("RHOAI SDG flow: stellar-peak-605")
    print("=========================================================\n")
    require_model_server(api_base, model_name)
    print(f"Loading SDG Hub flow: {target_flow}...")
    print(f"Reading Docling Markdown from: {DOCLING_MD_DIR}")
    sections = extract_markdown_sections(DOCLING_MD_DIR)
    if not sections:
        raise ValueError(
            f"No content sections found in {DOCLING_MD_DIR}. "
            "The Markdown has no usable headings after the table of contents."
        )
    print(f"Split Markdown into {len(sections)} section(s), skipping the table of contents...")
    for source_name, heading, _section_text in sections:
        print(f"  - {source_name}: {heading}")
    run_sdg_flow(sections)


if __name__ == "__main__":
    main()
