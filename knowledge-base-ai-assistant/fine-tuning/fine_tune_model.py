import os
import sys
import json
import torch
from boto3 import client
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer

print("=========================================================")
print("🚀 RHOAI Direct Engine: Production Native Training Loop")
print("=========================================================\n")

# =====================================================================
# 1. ENVIRONMENT SECURITY, S3 CONFIG & STABILITY BOUNDARIES
# =====================================================================
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

model_id = "ibm-granite/granite-3.0-8b-instruct"
source_dataset = "/opt/app-root/src/appdev-cop/knowledge-base-ai-assistant/sdg/synthetic_training_data.jsonl"
output_dir = os.getenv("LOCAL_MODEL_PATH", "./granite-fine-tuned-checkpoints")

endpoint_url = os.getenv("AWS_S3_ENDPOINT")
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
bucket_name = os.getenv("AWS_S3_BUCKET", "models")
s3_prefix = os.getenv("S3_PREFIX", "finetuned/custom/v1/").strip("/") + "/"
s3_uri = f"s3://{bucket_name}/{s3_prefix}"
upload_to_s3 = os.getenv("UPLOAD_TO_S3", "true").lower() in {"1", "true", "yes"}

# DEBUG VISIBILITY: Inspect exactly what environment variables are present in RAM
print("📡 Evaluated S3 Core Parameters from Environment:")
print(f"  - AWS_S3_ENDPOINT:    '{endpoint_url}'")
print(f"  - AWS_S3_BUCKET:      '{bucket_name}'")
print(f"  - S3_PREFIX:          '{s3_prefix}'")
print(f"  - UPLOAD_TO_S3:       {upload_to_s3}\n")

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
# 3. TOKENIZATION MANAGEMENT
# =====================================================================
print("🔧 Mapping token sequences from local workspace cache...")
tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
tokenizer.pad_token = tokenizer.eos_token

def tokenize_handler(examples):
    result = tokenizer(examples["text"], truncation=True, max_length=512, padding="max_length")
    result["labels"] = result["input_ids"].copy()
    return result

tokenized_dataset = raw_dataset.map(tokenize_handler, batched=True)

# =====================================================================
# 4. HARDWARE-OPTIMIZED MODEL ALLOCATION (YOUR ORIGINAL VERSION)
# =====================================================================
print("🧠 Allocating Granite 8B matrices into GPU Tensor Cores...")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    dtype=torch.bfloat16,             
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
os.makedirs(output_dir, exist_ok=True)
trainer.save_model(output_dir)
tokenizer.save_pretrained(output_dir)

metadata = {
    "base_model": model_id,
    "source_dataset": source_dataset,
    "artifact_format": "pytorch",
    "s3_destination": s3_uri,
}
with open(os.path.join(output_dir, "training_metadata.json"), "w", encoding="utf-8") as handle:
    json.dump(metadata, handle, indent=2)

artifact_files = os.listdir(output_dir)
has_config = "config.json" in artifact_files
has_weights = any(
    name == "pytorch_model.bin"
    or name == "model.safetensors"
    or (name.startswith("model-") and name.endswith(".safetensors"))
    for name in artifact_files
)
has_tokenizer = "tokenizer_config.json" in artifact_files

if not has_config or not has_weights or not has_tokenizer:
    print("Error: Incomplete fine-tuned artifact. Required before upload:")
    print(f"Found in '{output_dir}': {artifact_files}")
    sys.exit(1)

print(f"Local artifact ready at: {os.path.abspath(output_dir)}")
print(f"Files to upload ({len(artifact_files)}):")
for name in sorted(artifact_files):
    print(f"  - {name}")

# =====================================================================
# 8. PUSH FINE-TUNED ARTIFACT TO S3 / MINIO
# =====================================================================
if upload_to_s3:
    required_vars = {
        "AWS_S3_ENDPOINT": endpoint_url,
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key,
        "AWS_S3_BUCKET": bucket_name,
    }

    missing_vars = [var for var, val in required_vars.items() if not val]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    print(f"\nConnecting to MinIO/S3 API target endpoint: {endpoint_url}")
    print(f"Uploading all files to destination bucket path: {s3_uri}")

    try:
        # Explicit keyword assignment and timeouts prevent silent network drops
        s3_client = client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
	  #  verify=False,	
            config=Config(signature_version="s3v4", connect_timeout=10, read_timeout=30),
        )

        uploaded_files = []
        for root, _, files in os.walk(output_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                relative_path = os.path.relpath(local_path, output_dir)
                s3_file_key = f"{s3_prefix}{relative_path}".replace("\\", "/")
                
                # Added verbose printing to track upload progress file-by-file
                print(f"  ↑ Initializing push: {filename} ...")
                s3_client.upload_file(
                    Filename=local_path,
                    Bucket=bucket_name,
                    Key=s3_file_key,
                )
                uploaded_files.append(s3_file_key)
                print(f"    ↳ Complete: s3://{bucket_name}/{s3_file_key}")

        print(f"\n🎉 Successfully uploaded {len(uploaded_files)} object(s) to {s3_uri}")

    except (NoCredentialsError, PartialCredentialsError):
        print("Error: Invalid or incomplete AWS/MinIO credentials provided.")
        sys.exit(1)
    except ClientError as exc:
        print(f"Client Error: {exc.response['Error']['Message']}")
        sys.exit(1)
    except Exception as exc:
        print(f"An unexpected error occurred during transmission: {exc}")
        sys.exit(1)
else:
    print("\nSkipping S3 upload because UPLOAD_TO_S3=false")

print("\n=========================================================")
print("🎉 SUCCESS! Supervised Fine-Tuning complete.")
print(f"💾 Local artifact: {os.path.abspath(output_dir)}")
print(f"☁️  S3 artifact:   {s3_uri}")
print("=========================================================")
