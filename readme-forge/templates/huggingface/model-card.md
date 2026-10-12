---
# readme-forge HF model card. Keep only keys you can fill truthfully. See references/huggingface.md.
license: {{LICENSE_ID}}
language:
  - {{LANG_CODE}}
library_name: {{LIBRARY}}
pipeline_tag: {{PIPELINE_TAG}}
base_model: {{BASE_MODEL_ID}}
base_model_relation: {{adapter|merge|quantized|finetune}}
datasets:
  - {{DATASET_ID}}
metrics:
  - {{METRIC}}
tags:
  - {{TAG}}
---

# {{MODEL_NAME}}

{{ONE_PARAGRAPH_SUMMARY: what it is, what it was fine-tuned from, what it's for, headline result}}

## Model details

| | |
|---|---|
| **Developed by** | {{AUTHOR_OR_ORG}} |
| **Model type** | {{e.g. decoder-only transformer, LoRA adapter}} |
| **Language(s)** | {{…}} |
| **License** | {{LICENSE}} |
| **Finetuned from** | [{{BASE_MODEL_ID}}](https://huggingface.co/{{BASE_MODEL_ID}}) |
| **Repository** | {{GITHUB_URL}} |
| **Paper** | {{PAPER_URL or [More Information Needed]}} |
| **Demo** | {{SPACE_URL or [More Information Needed]}} |

## Uses

### Direct use

{{WHAT_USERS_CAN_DO_WITH_IT_AS_IS}}

### Downstream use

{{FINE-TUNING / INTEGRATION SCENARIOS}}

### Out-of-scope use

{{WHAT IT SHOULD NOT BE USED FOR, AND WHY}}

## Bias, risks, and limitations

{{KNOWN FAILURE MODES, DATA BIASES, LANGUAGES/DOMAINS IT IS WEAK ON}}

### Recommendations

{{HOW USERS SHOULD MITIGATE THE ABOVE}}

## How to get started

```python
{{RUNNABLE_SNIPPET}}
```

<!-- Examples:
transformers:   from transformers import pipeline; pipe = pipeline("{{PIPELINE_TAG}}", model="{{OWNER}}/{{NAME}}")
peft adapter:   base = AutoModelForCausalLM.from_pretrained("{{BASE_MODEL_ID}}"); model = PeftModel.from_pretrained(base, "{{OWNER}}/{{NAME}}")
gguf:           ollama run hf.co/{{OWNER}}/{{NAME}}   |   llama-cli -hf {{OWNER}}/{{NAME}} -p "…"
sentence-transformers: SentenceTransformer("{{OWNER}}/{{NAME}}").encode([...]) -->

## Training details

### Training data

{{DATASETS with links to their dataset cards; preprocessing}}

### Training procedure

| Hyperparameter | Value |
|---|---|
| learning_rate | {{…}} |
| batch_size | {{…}} |
| epochs / steps | {{…}} |
| optimizer | {{…}} |
| precision | {{bf16 / fp16}} |
| LoRA r / alpha | {{…}} |

**Compute:** {{N × GPU}} for {{HOURS}} hours.

## Evaluation

### Testing data, factors & metrics

{{BENCHMARKS, SPLITS, METRICS AND WHY}}

### Results

| Benchmark | Metric | {{BASE_MODEL}} | **{{MODEL_NAME}}** |
|---|---|---|---|
| {{…}} | {{…}} | {{…}} | **{{…}}** |

## Environmental impact

- **Hardware type:** {{…}}
- **Hours used:** {{…}}
- **Cloud provider / region:** {{…}}
- **Carbon emitted:** {{estimate via https://mlco2.github.io/impact}}

## Citation

```bibtex
{{BIBTEX}}
```

## Model card contact

{{CONTACT}}
