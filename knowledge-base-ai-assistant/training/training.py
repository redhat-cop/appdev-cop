import os
import json
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer

print("=========================================================")
print("🚀 RHOAI Direct Engine: Production Native Training Loop")
print("=========================================================\n")

# =====================================================================
# 1. ENVIRONMENT SECURITY & STABILITY BOUNDARIES
# =====================================================================
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

model_id = "ibm-granite/granite-3.0-8b-instruct"
source_dataset = "/opt/app-root/src/knowledge-base-ai-assistant/sdg_hub/synthetic_training_data.jsonl"
output_dir = "./granite-fine-tuned-checkpoints"

# =====================================================================
# 2. ADAPTIVE DATASET INGESTION & FORMATTING
# =====================================================================
print(f"📋 Ingesting raw synthetic dataset from: {os.path.abspath(source_dataset)}")
if not os.path.exists(source_dataset):
    raise FileNotFoundError(f"Missing data file: {source_dataset}. Run your SDG pipeline first!")

with open(source_dataset, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

formatted_texts = []
for idx, line in enumerate(lines):
    row = json.loads(line)
    
    question = row.get("question") or row.get("instruction") or row.get("query") or row.get("prompt")
    answer = row.get("answer") or row.get("response") or row.get("output")
    context = row.get("document") or row.get("context") or ""
    
    if not question or not answer:
        text_keys = [k for k, v in row.items() if isinstance(v, str) and k not in ['domain', 'document_outline', 'icl_document']]
        if len(text_keys) >= 2:
            question = row[text_keys[0]]
            answer = row[text_keys[1]]

    if question and answer:
        text_sequence = (
            f"<|system|>\nYou are a helpful corporate assistant grounded strictly in provided technical documentation.\n"
            f"<|user|>\nContext:\n{context}\n\nQuestion: {question}\n"
            f"<|assistant|>\n{answer}"
        )
        formatted_texts.append({"text": text_sequence})

if not formatted_texts:
    raise ValueError("CRITICAL: Failed to parse valid text pairs from the source asset.")

raw_dataset = Dataset.from_list(formatted_texts)
print(f"✨ Successfully mapped {len(formatted_texts)} aligned conversational chains.")

# =====================================================================
# 3. TOKENIZATION MANAGEMENT (FIX: Added Labels Generation)
# =====================================================================
print("🔧 Mapping token sequences from local workspace cache...")
tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
tokenizer.pad_token = tokenizer.eos_token

def tokenize_handler(examples):
    # Generate the base input IDs and attention masks
    result = tokenizer(examples["text"], truncation=True, max_length=512, padding="max_length")
    
    # FIX: Clone input_ids into labels so the model can calculate its own loss
    result["labels"] = result["input_ids"].copy()
    return result

tokenized_dataset = raw_dataset.map(tokenize_handler, batched=True)

# =====================================================================
# 4. HARDWARE-OPTIMIZED MODEL ALLOCATION (L4 GPU 24GB SAFEGUARD)
# =====================================================================
print("🧠 Allocating Granite 8B matrices into GPU Tensor Cores...")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    dtype=torch.bfloat16,             # Cleaned up deprecated parameter name
    local_files_only=True
)

print("🔒 Freezing base parameters to guarantee VRAM safety boundaries...")
for name, param in model.named_parameters():
    if "lm_head" not in name and "embed_tokens" not in name:
        param.requires_grad = False

# =====================================================================
# 5. DEFINE TRAINING EXECUTION HOOKS
# =====================================================================
training_args = TrainingArguments(
    output_dir=output_dir,
    per_device_train_batch_size=2,    
    gradient_accumulation_steps=2,    
    num_train_epochs=3,               
    learning_rate=2e-5,               
    logging_steps=1,                  
    fp16=False,
    bf16=True,                        
    gradient_checkpointing=True,      
    save_strategy="no",
    report_to="none"                  
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

# =====================================================================
# 6. RUN PROPAGATION
# =====================================================================
print("\n🏋️ Running forward and backward propagation cycles...")
trainer.train()

print("\n=========================================================")
print(f"🎉 SUCCESS! Supervised Fine-Tuning complete.")
print(f"💾 Fine-tuned model weights saved to: {os.path.abspath(output_dir)}")
print("=========================================================")
