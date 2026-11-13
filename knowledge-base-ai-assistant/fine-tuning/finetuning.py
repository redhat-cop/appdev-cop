import json
import os
import socket
import sys
from pathlib import Path

from boto3 import client
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

print("=========================================================")
print("Training Hub fine-tune")
print("=========================================================\n")

# =====================================================================
# 1. ENVIRONMENT SECURITY, S3 CONFIG & STABILITY BOUNDARIES
# =====================================================================
# The inner-loop pipeline reads this S3 path.
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# Unsloth patches transformers and peft at import time. training_hub
# imports those libraries, so Unsloth has to load first.
import unsloth  # noqa: F401

try:
    SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    SCRIPT_DIR = Path.cwd()

# model_id = "ibm-granite/granite-3.0-8b-instruct"
model_id = "ibm-granite/granite-4.2-8b"
# source_dataset = "/opt/app-root/src/appdev-cop/knowledge-base-ai-assistant/sdg/synthetic_training_data.jsonl"
# source_dataset = str(SCRIPT_DIR.parent / "sdg" / "synthetic_training_data.jsonl")
source_dataset = str(SCRIPT_DIR.parent / "sdg" / "sdg_out" / "synthetic_training_data.jsonl")
# source_dataset = str(SCRIPT_DIR.parent / "sdg" / "sdg_out" / "stellar_peak_raw.jsonl")
# output_dir = os.getenv("LOCAL_MODEL_PATH", "./granite-fine-tuned-checkpoints")
output_dir = str(SCRIPT_DIR / "lora-sft_output")
os.makedirs(output_dir, exist_ok=True)

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
# 2. MINIO UPLOAD
# =====================================================================
def upload_finetuned_artifact(local_dir: str) -> None:
    """Upload every file in the checkpoint folder to MinIO."""
    if not upload_to_s3:
        print("\nSkipping S3 upload because UPLOAD_TO_S3=false")
        return

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
            # verify=False,
            config=Config(signature_version="s3v4", connect_timeout=10, read_timeout=30),
        )

        uploaded_files = []
        for root, _, files in os.walk(local_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                relative_path = os.path.relpath(local_path, local_dir)
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


# =====================================================================
# 3. TRAINING DATA
# =====================================================================
def vllm_is_running(host: str = "127.0.0.1", port: int = 8000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


def clean_question(text: str) -> str:
    """Keep the question itself when the SDG row also saved the model's scratch text."""
    if "[QUESTION]" in text:
        text = text.split("[QUESTION]")[-1]
    if "[END]" in text:
        text = text.split("[END]")[0]
    if "</think>" in text:
        text = text.split("</think>")[-1]
    return " ".join(text.split())


UNKNOWN_ANSWER = "I don't know. Please ask based on the OpenShift AI guide."
SYSTEM_PROMPT = (
    "Answer from the OpenShift AI guide in one short reply. "
    "If the guide does not contain the answer, reply exactly: "
    + UNKNOWN_ANSWER
)
# SYSTEM_PROMPT = "You are a helpful corporate assistant grounded strictly in provided technical documentation."

UNKNOWN_QUESTIONS = [
    "What is the weather today?",
    "How do I bake an apple pie?",
    "Who won the world cup?",
    "What is the capital of France?",
]


def answer_text(text: str) -> str:
    """Drop the scratch reasoning and keep the answer from the training dataset."""
    if "</think>" in text:
        text = text.split("</think>", 1)[-1]
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("\\boxed{") or stripped.startswith(r"\boxed{"):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def write_messages_jsonl(raw_path: str, formatted_path: str) -> int:
    """Read the training dataset, keep each question and answer, and add a few 'I don't know' rows."""
    written = 0
    with open(raw_path, encoding="utf-8") as source, open(formatted_path, "w", encoding="utf-8") as output:
        def write_pair(question: str, answer: str) -> None:
            nonlocal written
            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer},
                ]
            }
            output.write(json.dumps(record) + "\n")
            written += 1

        for line in source:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if isinstance(row.get("messages"), list) and row["messages"]:
                question = next((item.get("content", "") for item in row["messages"] if item.get("role") == "user"), "")
                answer = next((item.get("content", "") for item in row["messages"] if item.get("role") == "assistant"), "")
            else:
                question = row.get("question") or row.get("instruction") or row.get("query") or ""
                answer = row.get("response") or row.get("answer") or ""
            question = clean_question(str(question))
            answer = answer_text(str(answer))
            if len(question) < 12 or question in {"...", "...\\n"} or not answer:
                continue
            write_pair(question, answer)

        for question in UNKNOWN_QUESTIONS:
            write_pair(question, UNKNOWN_ANSWER)
    return written


if vllm_is_running():
    raise SystemExit(
        "The vLLM server is still using the GPU on port 8000.\n"
        "Stop it first (pkill -f vllm), then run this file again."
    )

if not os.path.exists(source_dataset):
    raise FileNotFoundError(
        f"Missing training data: {source_dataset}. Run SDG first."
    )

# formatted_dataset = str(SCRIPT_DIR / "lora_training_data.jsonl")
formatted_dataset = str(Path(output_dir) / "lora_training_data.jsonl")
kept = write_messages_jsonl(source_dataset, formatted_dataset)
if kept == 0:
    raise ValueError(f"No question/answer rows found in {source_dataset}")

print(f"Training data: {formatted_dataset} ({kept} rows)")
print(f"Base model:    {model_id}")
print(f"Local output:  {os.path.abspath(output_dir)}")
# print(f"S3 destination:{s3_uri}")
print("Algorithm:     LoRA + SFT, 4-bit, one GPU")

# =====================================================================
# 4. LORA + SFT
# =====================================================================
from training_hub import lora_sft

lora_sft(
    model_path=model_id,
    data_path=formatted_dataset,
    ckpt_output_dir=output_dir,
    lora_r=16,
    lora_alpha=32,
    # num_epochs=1,
    num_epochs=3,
    learning_rate=2e-4,
    load_in_4bit=True,
)

# =====================================================================
# 5. LOCAL OUTPUT
# =====================================================================
# Upload stays in this file. Turn it back on when the MinIO bucket is ready.
# upload_finetuned_artifact(output_dir)

print("\n=========================================================")
print("LoRA fine-tuning complete.")
print(f"Local artifact: {os.path.abspath(output_dir)}")
# print(f"S3 artifact:    {s3_uri}")
print("S3 upload is commented out until the bucket is ready.")
print("=========================================================")
