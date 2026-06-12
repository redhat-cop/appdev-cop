import os
from datasets import Dataset
from sdg_hub import Flow, FlowRegistry

print("=========================================================")
print("📦 RHOAI Native Flow Registry: Guardrailed Context Setup")
print("=========================================================\n")

# 1. Discover built-in workflows
FlowRegistry.discover_flows()

# 2. Bind directly to the verified system flow template
target_flow = "Document Based Knowledge Tuning Dataset Generation Flow"
print(f"🎯 Target Blueprint: '{target_flow}'")

flow_path = FlowRegistry.get_flow_path(target_flow)
flow = Flow.from_yaml(flow_path)

# 3. Configure the local vLLM engine format using explicit keyword arguments
print("🔗 Linking pipeline to local vLLM loopback address...")
flow.set_model_config(
    model="hosted_vllm/ibm-granite/granite-3.0-8b-instruct",
    api_base="http://127.0.0.1:8000/v1",
    api_key="rhoai-local-token",
    max_tokens=512
)

# 4. Ingest the clean Markdown text created by Docling
context_file = "/opt/app-root/src/knowledge-base-ai-assistant/out/RHEL_AI-Inference.md"
if not os.path.exists(context_file):
    raise FileNotFoundError(f"Missing context asset: {context_file}. Run Docling first!")

print(f"📖 Ingesting and optimizing parsed document: {context_file}")
with open(context_file, "r", encoding="utf-8") as f:
    context_text = f.read()

# =====================================================================
# CONTEXT WINDOW GUARDRAIL: Cap character length to protect VRAM limit
# =====================================================================
# Your text hit 3,841 tokens. Limiting to 10,000 characters keeps the input
# around ~2,200 tokens, leaving plenty of space for the model to think and respond.
if len(context_text) > 10000:
    print("⚠️  Document text is dense! Truncating to safe character slice to prevent token overflow.")
    context_text = context_text[:10000]

# 5. Populate the exact validation schema required by the tuning blueprint
raw_data = [{
    "document": context_text,
    "document_outline": "Technical operational guide detailing core system infrastructure, platform features, and deployment rules.",
    "domain": "Enterprise Software and Cloud Infrastructure Operations",
    "icl_document": "Sample technical layout statement.",
    "icl_query_1": "What is the primary system deployment requirement?",
    "icl_query_2": "How does the core system handle runtime operational errors?",
    "icl_query_3": "Which management components are integrated by default?"
}]

dataset = Dataset.from_list(raw_data)

print("\n🚀 Passing tokens to the Granite 8B engine via Flow execution...")
result_dataset = flow.generate(dataset)

# 6. Output the generated dataset directly for Training Hub ingestion
output_file = "synthetic_training_data.jsonl"
result_dataset.to_json(output_file)

print("\n=========================================================")
print(f"🎉 SUCCESS! Native SDG Flow execution complete.")
print(f"💾 Dataset compiled for Training Hub: {os.path.abspath(output_file)}")
print("=========================================================")
