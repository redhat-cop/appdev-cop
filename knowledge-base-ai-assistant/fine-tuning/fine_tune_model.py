import os
import json
import torch
import boto3
from botocore.exceptions import BotoCoreError, ClientError
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

s3_bucket = os.getenv("S3_BUCKET", "models")
s3_prefix = os.getenv("S3_PREFIX", "finetuned/custom/v1/").strip("/") + "/"
s3_endpoint = os.getenv("S3_ENDPOINT_URL", "")
upload_to_s3 = os.getenv("UPLOAD_TO_S3", "true").lower() in {"1", "true", "yes"}

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

# =====================================================================
# 7. PERSIST FINE-TUNED ARTIFACT LOCALLY
# =====================================================================
print("\n💾 Persisting fine-tuned model and tokenizer to local workspace...")
trainer.save_model(output_dir)
tokenizer.save_pretrained(output_dir)

metadata = {
    "base_model": model_id,
    "source_dataset": source_dataset,
    "artifact_format": "pytorch",
    "s3_destination": f"s3://{s3_bucket}/{s3_prefix}",
}
with open(os.path.join(output_dir, "training_metadata.json"), "w", encoding="utf-8") as handle:
    json.dump(metadata, handle, indent=2)

print(f"Local artifact ready at: {os.path.abspath(output_dir)}")

# =====================================================================
# 8. PUSH FINE-TUNED ARTIFACT TO S3 / MINIO
# =====================================================================
def upload_directory_to_s3(local_dir: str, bucket: str, prefix: str) -> str:
    s3_uri = f"s3://{bucket}/{prefix}"
    s3_client_kwargs = {}
    if s3_endpoint:
        s3_client_kwargs["endpoint_url"] = s3_endpoint

    s3 = boto3.client("s3", **s3_client_kwargs)
    uploaded_files = []

    for root, _, files in os.walk(local_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_dir)
            object_key = f"{prefix}{relative_path}".replace("\\", "/")
            s3.upload_file(local_path, bucket, object_key)
            uploaded_files.append(object_key)

    print(f"Uploaded {len(uploaded_files)} object(s) to {s3_uri}")
    return s3_uri


if upload_to_s3:
    print(f"\n☁️ Uploading fine-tuned artifact to s3://{s3_bucket}/{s3_prefix}")
    try:
        s3_uri = upload_directory_to_s3(output_dir, s3_bucket, s3_prefix)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(
            f"Failed to upload fine-tuned model to s3://{s3_bucket}/{s3_prefix}. "
            f"Check S3/MinIO credentials and endpoint. Reason: {exc}"
        ) from exc
else:
    s3_uri = f"s3://{s3_bucket}/{s3_prefix}"
    print("\nSkipping S3 upload because UPLOAD_TO_S3=false")

print("\n=========================================================")
print("🎉 SUCCESS! Supervised Fine-Tuning complete.")
print(f"💾 Local artifact: {os.path.abspath(output_dir)}")
print(f"☁️  S3 artifact:   {s3_uri}")
print("=========================================================")
