import os
import socket
import torch
from pathlib import Path
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

print("=========================================================")
# print("💬 RHOAI Interactive Interface: Custom Granite 8B Chat")
print("LoRA adapter chat")
print("=========================================================\n")

# Maintain strict offline execution inside the OpenShift network
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

try:
    SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    SCRIPT_DIR = Path.cwd()

# Paths to your fine-tuned folder and base tokenizer definitions
# model_path = "./granite-fine-tuned-checkpoints"
model_path = str(SCRIPT_DIR.parent / "fine-tuning" / "lora-sft_output")
# base_model_id = "ibm-granite/granite-3.0-8b-instruct"
base_model_id = "ibm-granite/granite-4.2-8b"

adapter_file = Path(model_path) / "adapter_config.json"
if not adapter_file.is_file():
    raise SystemExit(
        f"No trained adapter at {model_path}.\n"
        "Expected adapter_config.json from the LoRA run."
    )


def vllm_is_running(host: str = "127.0.0.1", port: int = 8000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


if vllm_is_running():
    raise SystemExit(
        "The vLLM server is still using the GPU on port 8000.\n"
        "Stop it first (pkill -f vllm), then run this file again."
    )

print(f"Base model:      {base_model_id}")
print(f"Trained adapter: {model_path}")
print("Loading the base model in 4-bit, then attaching the LoRA adapter...")
tokenizer = AutoTokenizer.from_pretrained(base_model_id, local_files_only=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Fallback mechanism in case final weights need to pull from the last active memory state
# try:
#     model = AutoModelForCausalLM.from_pretrained(
#         model_path,
#         device_map="auto",
#         dtype=torch.bfloat16,
#         local_files_only=True
#     )
# except Exception:
#     print("ℹ️ Direct path fallback: Loading base model with custom configuration adapter layers...")
#     model = AutoModelForCausalLM.from_pretrained(
#         base_model_id,
#         device_map="auto",
#         dtype=torch.bfloat16,
#         local_files_only=True
#     )
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
print("Trained adapter is attached. Answers below come from that adapter.")

# The same anchoring system prompt used during the training loop
system_prompt = "You are a helpful corporate assistant grounded strictly in provided technical documentation."

print("\nLoRA chat is ready. Type 'exit' or 'quit' to stop.")
print("Paste a training question with its context, then a line that says END:")
print("Context:")
print("<section text>")
print()
print("Question: <question from that section>")
print("END")
print("=========================================================\n")

while True:
    try:
        print("👤 You:")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            if not lines and line.strip().lower() in ["exit", "quit"]:
                lines = [line]
                break
            lines.append(line)
        user_input = "\n".join(lines).strip()
        if user_input.lower() in ["exit", "quit"]:
            print("\n👋 Closing the interactive session. Excellent work on the training run!")
            break

        if not user_input:
            continue

        # Reconstruct the exact structural ChatML format the model was trained on
        # prompt = (
        #     f"<|system|>\n{system_prompt}\n"
        #     f"<|user|>\n{user_input}\n"
        #     f"<|assistant|>\n"
        # )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        # Tokenize prompt inputs and move tensors to the GPU
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.3,     # Lower temperature keeps the model grounded and factual
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode output tokens and strip out systemic tokens to isolate the raw answer
        # full_text = tokenizer.decode(outputs[0], skip_special_tokens=False)
        # response = full_text.split("<|assistant|>\n")[-1].replace(tokenizer.eos_token, "").strip()
        new_tokens = outputs[0][inputs["input_ids"].shape[-1]:]
        response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        print(f"\nLoRA adapter: {response}\n")
        print("-" * 60)

    except KeyboardInterrupt:
        print("\n👋 Session interrupted.")
        break
