import os
import re
from pathlib import Path

from datasets import Dataset
from sdg_hub import Flow, FlowRegistry

print("=========================================================")
print("📦 RHOAI Native Flow Registry: Multi-Row Generation")
print("=========================================================\n")

# 1. Discover built-in workflows
FlowRegistry.discover_flows()

# 2. Bind directly to the verified system flow template
# target_flow = "Document Based Knowledge Tuning Dataset Generation Flow"
# flow_path = FlowRegistry.get_flow_path(target_flow)
# The built-in flow's own default model is openai/gpt-oss-120b.
# set_model_config below replaces that default with the local Granite server.
target_flow = "stellar-peak-605"  # Document Based Knowledge Tuning
flow_path = FlowRegistry.get_flow_path_safe(target_flow)
flow = Flow.from_yaml(flow_path)

# 3. Configure local vLLM engine
flow.set_model_config(
    # model="hosted_vllm/ibm-granite/granite-3.0-8b-instruct",
    model="hosted_vllm/ibm-granite/granite-4.2-8b",
    api_base="http://127.0.0.1:8000/v1",
    api_key="rhoai-local-token",
    max_tokens=512
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

try:
    SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    SCRIPT_DIR = Path.cwd()

DOCLING_OUT_DIR = SCRIPT_DIR.parent / "docling" / "docling_out"
HEADING_LINE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def is_table_of_contents(heading: str) -> bool:
    normalized = re.sub(r"[^a-z]+", " ", heading.lower()).strip()
    return normalized in {"table of contents", "contents", "toc"} or normalized.startswith(
        "table of contents"
    )


def split_markdown_sections(markdown: str) -> list[tuple[str, str]]:
    """Return (heading, section text) pairs. Text before the first heading is skipped."""
    sections = []
    heading = None
    lines: list[str] = []

    def save_current() -> None:
        if heading is None:
            return
        body = "\n".join(lines[1:]).strip()
        if not body or is_table_of_contents(heading):
            return
        sections.append((heading, "\n".join(lines).strip()))

    for line in markdown.splitlines():
        match = HEADING_LINE.match(line)
        if match:
            save_current()
            heading = match.group(2).strip()
            lines = [line]
        elif heading is not None:
            lines.append(line)

    save_current()
    return sections


def load_docling_sections(docling_out_dir: Path) -> list[tuple[str, str, str]]:
    if not docling_out_dir.is_dir():
        raise FileNotFoundError(
            f"Missing Docling output folder: {docling_out_dir}. Run Docling first!"
        )

    markdown_files = sorted(
        path for path in docling_out_dir.rglob("*.md") if path.is_file()
    )
    if not markdown_files:
        raise FileNotFoundError(
            f"No Markdown files in {docling_out_dir}. Run Docling first!"
        )

    sections = []
    for markdown_file in markdown_files:
        text = markdown_file.read_text(encoding="utf-8")
        for heading, section_text in split_markdown_sections(text):
            sections.append((markdown_file.name, heading, section_text))
    return sections


print(f"Reading Docling Markdown from: {DOCLING_OUT_DIR}")
sections = load_docling_sections(DOCLING_OUT_DIR)
if not sections:
    raise ValueError(
        f"No content sections found in {DOCLING_OUT_DIR}. "
        "The Markdown has no usable headings after the table of contents."
    )
print(f"Split Markdown into {len(sections)} section(s), skipping the table of contents...")
for source_name, heading, _section_text in sections:
    print(f"  - {source_name}: {heading}")

raw_data = []
for _source_name, heading, section_text in sections:
    raw_data.append({
        "document": section_text,
        # "document_outline": "Red Hat OpenShift AI Self-Managed Getting Started Guide.",
        "document_outline": heading,
        "domain": "Enterprise AI",
        "icl_document": "RedHat OpenShift AI 3.5",
        "icl_query_1": "What are the core steps in the OpenShift AI workflow?",
        "icl_query_2": "How do I set up a project and workbench?",
        "icl_query_3": "Explain the difference between model serving and AI pipelines.",
        "icl_query_4": "How do connections help with Object Storage?",
        "icl_query_5": "How do workbenches help with model development and training?"
    })

dataset = Dataset.from_list(raw_data)

print("\n🚀 Passing chunks to the Granite 8B engine via Flow execution...")
result_dataset = flow.generate(dataset)

# 5. Output the multi-row dataset for Training Hub ingestion
output_file = "synthetic_training_data.jsonl"
result_dataset.to_json(output_file)

print("\n=========================================================")
print(f"🎉 SUCCESS! Native SDG Flow execution complete.")
print(f"💾 Multi-row dataset compiled: {os.path.abspath(output_file)}")
print("=========================================================")
