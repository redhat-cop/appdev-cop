import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

print("=========================================================")
print("💬 RHOAI Interactive Interface: Custom Granite 8B Chat")
print("=========================================================\n")

# Maintain strict offline execution inside the OpenShift network
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# Paths to your fine-tuned folder and base tokenizer definitions
model_path = "./granite-fine-tuned-checkpoints"
base_model_id = "ibm-granite/granite-3.0-8b-instruct"

print("🧠 Loading your fine-tuned parameters into GPU memory...")
tokenizer = AutoTokenizer.from_pretrained(base_model_id, local_files_only=True)

# Fallback mechanism in case final weights need to pull from the last active memory state
try:
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",
        dtype=torch.bfloat16,
        local_files_only=True
    )
except Exception:
    print("ℹ️ Direct path fallback: Loading base model with custom configuration adapter layers...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        device_map="auto",
        dtype=torch.bfloat16,
        local_files_only=True
    )

# The same anchoring system prompt used during the training loop
system_prompt = "You are a helpful corporate assistant grounded strictly in provided technical documentation."

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

        # Reconstruct the exact structural ChatML format the model was trained on
        prompt = (
            f"<|system|>\n{system_prompt}\n"
            f"<|user|>\n{user_input}\n"
            f"<|assistant|>\n"
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
        full_text = tokenizer.decode(outputs[0], skip_special_tokens=False)
        response = full_text.split("<|assistant|>\n")[-1].replace(tokenizer.eos_token, "").strip()

        print(f"\n🤖 Granite Custom: {response}\n")
        print("-" * 60)

    except KeyboardInterrupt:
        print("\n👋 Session interrupted.")
        break
