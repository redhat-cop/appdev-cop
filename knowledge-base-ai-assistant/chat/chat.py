import os
import socket
import torch
from pathlib import Path
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

print("=========================================================")
print("💬 RHOAI Interactive Interface: Custom Granite 8B Chat")
print("=========================================================\n")

# Maintain strict offline execution inside the OpenShift network
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

SCRIPT_DIR = Path(__file__).resolve().parent

# Paths to your fine-tuned folder and base tokenizer definitions
# model_path = "./granite-fine-tuned-checkpoints"
model_path = str(SCRIPT_DIR.parent / "fine-tuning" / "lora-sft_output")
# model_path = str(SCRIPT_DIR.parent / "fine-tuning" / "granite-fine-tuned-checkpoints")
# base_model_id = "ibm-granite/granite-3.0-8b-instruct"
base_model_id = "ibm-granite/granite-4.2-8b"

if not (Path(model_path) / "adapter_config.json").is_file():
    raise SystemExit(f"No trained adapter at {model_path}")


def vllm_is_running(host="127.0.0.1", port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


if vllm_is_running():
    raise SystemExit(
        "The vLLM server is still using the GPU on port 8000.\n"
        "Stop it first (pkill -f vllm), then run this file again."
    )

print("🧠 Loading your fine-tuned parameters into GPU memory...")
print(f"Base model:      {base_model_id}")
print(f"Trained adapter: {model_path}")

tokenizer = AutoTokenizer.from_pretrained(base_model_id, local_files_only=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    device_map="auto",
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
    ),
    local_files_only=True,
)
model = PeftModel.from_pretrained(base_model, model_path, local_files_only=True)
model.eval()

# system_prompt = "You are a helpful corporate assistant grounded strictly in provided technical documentation."
# system_prompt = (
#     "Answer from the OpenShift AI guide in one short reply. "
#     "If the guide does not contain the answer, reply exactly: "
#     "I don't know. Please ask based on the OpenShift AI guide."
# )
# system_prompt = (
#     "Reply with the answer only, in one short reply. "
#     "Do not describe your reasoning. "
#     "If the OpenShift AI guide does not contain the answer, reply exactly: "
#     "We don't have that information."
# )
UNKNOWN_ANSWER = "We don't have that information."
system_prompt = (
    "Answer in a few clear sentences. "
    "State the facts directly, with no scratch notes and no mention of a document. "
    "If the OpenShift AI guide does not contain the answer, reply exactly: "
    + UNKNOWN_ANSWER
)


def visible_answer(text: str) -> str:
    """Keep the answer and drop the scratch reasoning."""
    if "</think>" in text:
        text = text.split("</think>", 1)[-1]
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("\\boxed{") or stripped.startswith(r"\boxed{"):
            continue
        kept.append(line)
    text = "\n".join(kept).strip()
    return text or UNKNOWN_ANSWER


print("\n🤖 Custom Granite Model is ready! Type 'exit' or 'quit' to stop.")
print("=========================================================\n")

while True:
    try:
        user_input = input("👤 You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("\n👋 Closing the interactive session. Excellent work on the training run!")
            break

        if not user_input.strip():
            continue

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        try:
            # thinking=False is the Granite 3.2 switch and does not turn off Granite 4.2.
            # enable_thinking=False stops Granite 4.2 from writing the scratch notes first.
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                # thinking=False,
                enable_thinking=False,
            )
        except Exception:
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                # max_new_tokens=256,
                # max_new_tokens=768,
                max_new_tokens=1024,
                # temperature=0.3,
                # do_sample=True,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        new_tokens = outputs[0][inputs["input_ids"].shape[-1] :]
        response = visible_answer(tokenizer.decode(new_tokens, skip_special_tokens=True))

        print(f"\n🤖 Granite Custom: {response}\n")
        print("-" * 60)

    except KeyboardInterrupt:
        print("\n👋 Session interrupted.")
        break
