---
base_model: ibm-granite/granite-4.2-8b
library_name: peft
model_name: lora-sft_output
tags:
- base_model:adapter:ibm-granite/granite-4.2-8b
- lora
- sft
- transformers
- trl
- unsloth
licence: license
pipeline_tag: text-generation
---

# Model Card for lora-sft_output

This model is a fine-tuned version of [ibm-granite/granite-4.2-8b](https://huggingface.co/ibm-granite/granite-4.2-8b).
It has been trained using [TRL](https://github.com/huggingface/trl).

## Quick start

```python
from transformers import pipeline

question = "If you had a time machine, but could only go to the past or the future once and never return, which would you choose and why?"
generator = pipeline("text-generation", model="None", device="cuda")
output = generator([{"role": "user", "content": question}], max_new_tokens=128, return_full_text=False)[0]
print(output["generated_text"])
```

## Training procedure

 



This model was trained with SFT.

### Framework versions

- PEFT 0.20.0
- TRL: 1.7.1
- Transformers: 5.13.0
- Pytorch: 2.11.0
- Datasets: 5.0.1
- Tokenizers: 0.22.2

## Citations



Cite TRL as:
    
```bibtex
@software{vonwerra2020trl,
  title   = {{TRL: Transformers Reinforcement Learning}},
  author  = {von Werra, Leandro and Belkada, Younes and Tunstall, Lewis and Beeching, Edward and Thrush, Tristan and Lambert, Nathan and Huang, Shengyi and Rasul, Kashif and Gallouédec, Quentin},
  license = {Apache-2.0},
  url     = {https://github.com/huggingface/trl},
  year    = {2020}
}
```