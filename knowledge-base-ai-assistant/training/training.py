import os
import json
from training_hub import sft

print("=========================================================")
print("🚀 RHOAI Native Training Hub: Diagnostic SFT Active")
print("=========================================================\n")

source_dataset = "/opt/app-root/src/knowledge-base-ai-assistant/sdg_hub/synthetic_training_data.jsonl"
formatted_dataset = "formatted_training_data.jsonl"
output_dir = "./granite-fine-tuned-checkpoints"
data_out_dir = "./training_data_output"

if not os.path.exists(source_dataset):
    raise FileNotFoundError(f"Could not find {source_dataset}. Run sdg.py first.")

# Read the file contents safely
with open(source_dataset, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

if not lines:
    raise ValueError(f"CRITICAL: {source_dataset} is completely empty! Your SDG flow failed to write data.")

# 1. Print out keys for immediate visibility
sample_row = json.loads(lines[0])
print(f"📋 Detected Dataset Columns/Keys: {list(sample_row.keys())}")

formatted_rows = []

for idx, line in enumerate(lines):
    row = json.loads(line)
    
    # If the flow output format already contains a valid messages list, use it directly
    if "messages" in row and isinstance(row["messages"], list):
        formatted_rows.append(row)
        continue
        
    # Smart extraction: check all common names for queries and answers
    question = row.get("question") or row.get("instruction") or row.get("query") or row.get("prompt") or row.get("user")
    answer = row.get("answer") or row.get("response") or row.get("output") or row.get("completion") or row.get("assistant")
    context = row.get("document") or row.get("context") or ""
    
    # Fallback: if keys are completely customized, grab the first non-document text fields
    if not question or not answer:
        text_keys = [k for k, v in row.items() if isinstance(v, str) and k not in ['domain', 'document_outline', 'icl_document']]
        if len(text_keys) >= 2:
            question = row[text_keys[0]]
            answer = row[text_keys[1]]
            
    if question and answer:
        user_content = f"Context:\n{context}\n\nQuestion: {question}" if context else str(question)
        
        # Build the exact three-tier structure expected by InstructLab-Training
        formatted_rows.append({
            "messages": [
                {"role": "system", "content": "You are a helpful corporate assistant grounded strictly in provided technical documentation."},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": str(answer)}
            ]
        })
    else:
        print(f"⚠️ Skipping Row {idx}: Unable to parse text content from keys {list(row.keys())}")

print(f"✨ Successfully mapped and formatted {len(formatted_rows)}/{len(lines)} training samples.")

if len(formatted_rows) == 0:
    print("\n❌ ERROR: Your dataset mapping resulted in 0 examples. Inspect the raw row structure below:")
    print(json.dumps(sample_row, indent=2))
    raise ValueError("Aborting training: Dataset formatting yielded an empty array.")

# Write the validated JSON Lines data back to disk
with open(formatted_dataset, "w", encoding="utf-8") as f:
    for row in formatted_rows:
        f.write(json.dumps(row) + "\n")

# 2. Trigger the training pipeline
print("\n🧠 Passing aligned data into the GPU execution engine...")
result = sft(
    model_path="ibm-granite/granite-3.0-8b-instruct",
    model_name_or_path="ibm-granite/granite-3.0-8b-instruct",
    data_path=formatted_dataset,
    ckpt_output_dir=output_dir,
    data_output_dir=data_out_dir,
    num_epochs=3,                     
    effective_batch_size=4,           
    learning_rate=1e-5,               
    max_seq_len=1024,                 
    max_tokens_per_gpu=2048,
    max_batch_len=2048                
)

print("\n=========================================================")
print(f"🎉 SUCCESS! Supervised Fine-Tuning complete.")
print(f"💾 Custom model weights compiled at: {os.path.abspath(output_dir)}")
print("=========================================================")
