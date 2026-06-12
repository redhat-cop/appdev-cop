import os
from datasets import Dataset
from sdg_hub import Flow, FlowRegistry

print("=========================================================")
print("📦 RHOAI Native Flow Registry: Multi-Row Generation")
print("=========================================================\n")

# 1. Discover built-in workflows
FlowRegistry.discover_flows()

# 2. Bind directly to the verified system flow template
target_flow = "Document Based Knowledge Tuning Dataset Generation Flow"
flow_path = FlowRegistry.get_flow_path(target_flow)
flow = Flow.from_yaml(flow_path)

# 3. Configure local vLLM engine
flow.set_model_config(
    model="hosted_vllm/ibm-granite/granite-3.0-8b-instruct",
    api_base="http://127.0.0.1:8000/v1",
    api_key="",
    max_tokens=512
)

# 4. Ingest the clean Markdown text created by Docling
context_file = "/opt/app-root/src/knowledge-base-ai-assistant/out/RHEL_AI-Inference.md"
if not os.path.exists(context_file):
    raise FileNotFoundError(f"Missing context asset: {context_file}. Run Docling first!")

with open(context_file, "r", encoding="utf-8") as f:
    context_text = f.read()

# =====================================================================
# FIX: Chunk text into multiple sections to generate a multi-row dataset
# =====================================================================
chunk_size = 2500
chunks = [context_text[i:i+chunk_size] for i in range(0, len(context_text), chunk_size)]
chunks = chunks[:5]  # Cap at 5 rows to keep your live demo execution fast

print(f"🧩 Split document into {len(chunks)} distinct segments for generation...")

raw_data = []
for chunk in chunks:
    raw_data.append({
        "document": chunk,
        "document_outline": "Technical operational guide detailing core system infrastructure, platform features, and deployment rules.",
        "domain": "Enterprise Software and Cloud Infrastructure Operations",
        "icl_document": "Sample technical layout statement.",
        "icl_query_1": "What is the primary system deployment requirement?",
        "icl_query_2": "How does the core system handle runtime operational errors?",
        "icl_query_3": "Which management components are integrated by default?"
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
