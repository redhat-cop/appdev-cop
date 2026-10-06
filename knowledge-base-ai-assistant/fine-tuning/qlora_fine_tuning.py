import os
import sys
import json
from boto3 import client
from botocore.config import Config

# IMPORT TRUTHS: Import the platform's official LoRA execution function
from training_hub import lora_sft

print("=========================================================")
print("🚀 RHOAI Training Hub: Self-Healing QLoRA Loop")
print("=========================================================\n")

# =====================================================================
# 1. ENVIRONMENT ISOLATION & S3 CONFIGURATION
# =====================================================================
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

source_dataset = "/opt/app-root/src/appdev-cop/knowledge-base-ai-assistant/sdg/synthetic_training_data.jsonl"
formatted_dataset_path = "./formatted_training_data.jsonl"
output_dir = os.getenv("LOCAL_MODEL_PATH", "./granite-fine-tuned-checkpoints")

endpoint_url = os.getenv("AWS_S3_ENDPOINT")
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
bucket_name = os.getenv("AWS_S3_BUCKET", "models")
s3_prefix = os.getenv("S3_PREFIX", "finetuned/custom/v1/").strip("/") + "/"
s3_uri = f"s3://{bucket_name}/{s3_prefix}"
upload_to_s3 = os.getenv("UPLOAD_TO_S3", "true").lower() in {"1", "true", "yes"}

# =====================================================================
# 2. DYNAMIC DEEP SNAPSHOT PATH RESOLUTION
# =====================================================================
print("🔍 Resolving the exact nested snapshot folder...")
base_repo_dir = "/opt/app-root/src/.cache/huggingface/hub/models--ibm-granite--granite-3.0-8b-instruct"
snapshots_dir = os.path.join(base_repo_dir, "snapshots")

if not os.path.exists(snapshots_dir):
    print(f"❌ CRITICAL ERROR: The snapshots folder does not exist at: {snapshots_dir}")
    print("Please make sure the base model was fully cached on your PVC storage.")
    sys.exit(1)

# Find any subdirectories inside the snapshots folder (this represents the hash folder)
hash_folders = [
    os.path.join(snapshots_dir, d) for d in os.listdir(snapshots_dir)
    if os.path.isdir(os.path.join(snapshots_dir, d))
]

if not hash_folders:
    print(f"❌ CRITICAL ERROR: The snapshots directory '{snapshots_dir}' is empty.")
    sys.exit(1)

# Grab the first matching hash folder (Hugging Face caches only one active snapshot at a time)
model_id = hash_folders[0]
print(f"🎯 Path Resolved! Target snapshot folder is:\n   ↳ {model_id}\n")

# =====================================================================
# 3. FIX FOR FLEX_ATTENTION DROPOUT BUG IN GRANITE 3.0
# =====================================================================
config_path = os.path.join(model_id, "config.json")
if os.path.exists(config_path):
    print("🛠️ Applying local fix: disabling attention dropout in config.json to satisfy flex_attention...")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # Disable all potential attention and layer dropout fields to satisfy the backend
        config_data["attention_dropout"] = 0.0
        config_data["attention_probs_dropout_prob"] = 0.0
        config_data["dropout"] = 0.0
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        print("✅ config.json successfully patched! attention_dropout set to 0.0.\n")
    except Exception as e:
        print(f"⚠️ Warning: Could not patch config.json: {e}\n")
else:
    print(f"❌ Error: 'config.json' was not found in {model_id}")
    sys.exit(1)

# =====================================================================
# 4. DATA PREPROCESSING & SCHEMA ALIGNMENT
# =====================================================================
print(f"📋 Ingesting raw synthetic dataset from: {os.path.abspath(source_dataset)}")
if not os.path.exists(source_dataset):
    raise FileNotFoundError(f"Missing data file: {source_dataset}")

with open(source_dataset, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"🔧 Restructuring text records into chat-formatted system blocks...")
with open(formatted_dataset_path, "w", encoding="utf-8") as out_f:
    for line in lines:
        row = json.loads(line)
        question = row.get("question") or row.get("instruction") or row.get("query")
        answer = row.get("answer") or row.get("response")
        context = row.get("document") or row.get("context") or ""
        
        if question and answer:
            message_structure = {
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a helpful corporate assistant grounded strictly in provided technical documentation."
                    },
                    {
                        "role": "user", 
                        "content": f"Context:\n{context}\n\nQuestion: {question}"
                    },
                    {
                        "role": "assistant", 
                        "content": answer
                    }
                ]
            }
            out_f.write(json.dumps(message_structure) + "\n")

print(f"✨ Conversational records prepared at: {os.path.abspath(formatted_dataset_path)}")

# =====================================================================
# 5. EXECUTE NATIVE QLORA + SFT WITH UNSLOTH OPTIMIZATION
# =====================================================================
print("\n🏋️ Initializing RHOAI LoRA Fine-Tuning Block...")

result = lora_sft(
    model_path=model_id,                  # Points directly to snapshots/hash_folder/
    data_path=formatted_dataset_path,     
    ckpt_output_dir=output_dir,           
    lora_r=16,                            
    lora_alpha=32,                        
    num_epochs=3,                         
    learning_rate=2e-4,
    load_in_4bit=True                     # Keeps model footprints safe inside 16 GB limits
)

print("\n💾 Training complete. Checking compiled adapter outputs...")

# =====================================================================
# 6. VERIFY ARTIFACT INTEGRITY
# =====================================================================
metadata = {
    "base_model": "ibm-granite/granite-3.0-8b-instruct",
    "source_dataset": source_dataset,
    "artifact_format": "lora_adapters",
    "s3_destination": s3_uri,
}
with open(os.path.join(output_dir, "training_metadata.json"), "w", encoding="utf-8") as handle:
    json.dump(metadata, handle, indent=2)

artifact_files = os.listdir(output_dir)
has_config = "adapter_config.json" in artifact_files
has_weights = any("adapter_model" in name for name in artifact_files)

if not has_config or not has_weights:
    print(f"Error: LoRA adapter file integrity check failed in '{output_dir}'.")
    sys.exit(1)

print(f"Adapters compiled completely at: {os.path.abspath(output_dir)}")

# =====================================================================
# 7. PUSH LIGHTWEIGHT ADAPTERS TO MINIO / S3
# =====================================================================
if upload_to_s3:
    print(f"\nConnecting to MinIO/S3 API target endpoint: {endpoint_url}")
    try:
        s3_client = client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4", connect_timeout=10, read_timeout=30),
        )

        uploaded_files = []
        for root, _, files in os.walk(output_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                relative_path = os.path.relpath(local_path, output_dir)
                s3_file_key = f"{s3_prefix}{relative_path}".replace("\\", "/")
                
                print(f"  ↑ Pushing adapter file: {filename} ...")
                s3_client.upload_file(Filename=local_path, Bucket=bucket_name, Key=s3_file_key)
                uploaded_files.append(s3_file_key)

        print(f"\n🎉 Successfully uploaded {len(uploaded_files)} object(s) to {s3_uri}")
    except Exception as exc:
        print(f"S3 Upload failed: {exc}")
        sys.exit(1)

print("\n=========================================================")
print("🎉 SUCCESS! RHOAI Training Hub QLoRA + SFT Run Complete.")
print(f"💾 Local adapter directory: {os.path.abspath(output_dir)}")
print(f"☁️  S3 bucket location:    {s3_uri}")
print("=========================================================")
