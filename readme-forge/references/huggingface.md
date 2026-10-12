# Hugging Face cards (model · dataset · Space)

On the Hub, `README.md` = YAML frontmatter (machine metadata) + Markdown body (human card). The metadata drives search filters, the license display, the inference widget, eval leaderboards, the model tree, and Space builds. Validate it with `python scripts/score_readme.py README.md --hf`.

**General rules**
- Use only valid keys and values. If you don't know a value, omit the key. Don't invent values.
- Body sections whose information is missing get `[More Information Needed]`, the Hub's own convention, rather than made-up text.
- Code snippets must use the real repo id (`OWNER/NAME`) and the right library class.
- Mirror important GitHub README facts here and cross-link both ways.

## Model card

### Frontmatter
```yaml
---
license: apache-2.0               # Hub license id; "other" requires license_name + license_link
language:                          # ISO 639-1 codes
  - en
library_name: transformers         # REQUIRED explicitly for repos created after Aug 2024 (transformers, diffusers, peft, sentence-transformers, timm, gguf, mlx, onnx, keras, sklearn, …)
pipeline_tag: text-generation      # enables the widget and task filter
tags:
  - lora
  - code
base_model: meta-llama/Llama-3.1-8B-Instruct   # string or list (merges)
base_model_relation: adapter       # adapter | merge | quantized | finetune (inferred if omitted)
datasets:
  - OWNER/dataset-name
metrics:
  - accuracy
new_version: OWNER/newer-model     # optional: points users to a newer model
thumbnail: https://…/thumb.png     # optional
model-index:                       # optional: renders an eval-results widget
  - name: NAME
    results:
      - task:
          type: text-generation
        dataset:
          name: HumanEval
          type: openai_humaneval
        metrics:
          - type: pass@1
            value: 0.623          # REAL numbers only
            name: pass@1
---
```
Detect from files:
- `adapter_config.json` → `library_name: peft`, `base_model` from `base_model_name_or_path`, `base_model_relation: adapter`.
- `*.gguf` → `library_name: gguf` (or omit), `base_model_relation: quantized`.
- `config.json` `architectures` gives the model class. `model_type` + task gives the `pipeline_tag`.
- `modules.json` / `sentence_bert_config.json` → `library_name: sentence-transformers`, `pipeline_tag: sentence-similarity`.
- `model_index.json` (diffusers) → `library_name: diffusers`, `pipeline_tag: text-to-image` (verify).
- `special tag not-for-all-audiences` for NSFW-capable models.

### Body sections (template: `templates/huggingface/model-card.md`)
1. **Title + one-paragraph summary**: what the model is, its base, what it's for.
2. **Model details**: developed by, model type, languages, license, finetuned from, and sources (repo, paper, demo).
3. **Uses**: direct use, downstream use, and **out-of-scope use**.
4. **Bias, risks, and limitations**, plus recommendations.
5. **How to get started**: a runnable snippet of ≤ 15 lines (transformers pipeline or the library's API). For adapters, show loading the base model plus the adapter. For GGUF, show the llama.cpp / ollama command.
6. **Training details**: training data (link the dataset card), procedure, hyperparameters table, compute (hardware, hours).
7. **Evaluation**: testing data, factors, metrics, and a **results table**.
8. **Environmental impact** (optional): hardware type, hours, cloud region, CO₂ estimate (ML CO2 calculator).
9. **Citation** (BibTeX). **Model card authors / contact**.

## Dataset card

### Frontmatter
```yaml
---
pretty_name: My Dataset
license: cc-by-4.0
language:
  - en
task_categories:          # e.g. text-classification, question-answering, text-generation, image-classification, automatic-speech-recognition, tabular-classification
  - question-answering
task_ids:
  - extractive-qa         # optional, finer grained
size_categories:
  - 10K<n<100K            # n<1K | 1K<n<10K | 10K<n<100K | 100K<n<1M | 1M<n<10M | 10M<n<100M | 100M<n<1B | 1B<n<10B | 10B<n<100B | 100B<n<1T | n>1T
tags:
  - synthetic
annotations_creators: [expert-generated]   # optional
source_datasets: [original]                # optional
configs:                  # maps files → configs/splits (lets the viewer + load_dataset work without a script)
  - config_name: default
    data_files:
      - split: train
        path: data/train-*.parquet
      - split: test
        path: data/test-*.parquet
---
```
Body (template `templates/huggingface/dataset-card.md`): summary, supported tasks, languages, **dataset structure** (an example instance, a fields table with types, a splits table with row counts), creation (curation rationale, source data, annotation process, personal/sensitive info), considerations (social impact, bias, limitations), usage (`load_dataset("OWNER/NAME")` snippet), license and citation.

Row counts and fields come from real files. If you can read a parquet/csv/jsonl header, use it.

## Space README (configuration)

```yaml
---
title: My Demo                 # display name
emoji: 🚀                      # single emoji
colorFrom: indigo              # ONLY: red, yellow, green, blue, indigo, purple, pink, gray
colorTo: purple
sdk: gradio                    # gradio | docker | static  (streamlit Spaces now run via docker template)
sdk_version: 5.0.0             # match requirements.txt gradio version (read it; don't guess)
python_version: "3.10"         # optional, default 3.10
app_file: app.py               # gradio/streamlit entry
app_port: 7860                 # docker only
short_description: One line shown on the Space card (≤ 60 chars)
license: mit
pinned: false
models:                        # Hub models used (links them)
  - OWNER/model
datasets:
  - OWNER/dataset
tags: [demo]
suggested_hardware: t4-small   # optional (cpu-basic, cpu-upgrade, t4-small, t4-medium, a10g-small, l4x1, a100-large, …)
hf_oauth: false                # optional "Sign in with HF"
fullWidth: false
header: default                # default | mini
disable_embedding: false
---
```
Detect it this way: `app.py` importing gradio gives `sdk: gradio`, and `sdk_version` comes from the `gradio==` pin in requirements.txt. A `Dockerfile` gives `sdk: docker` (read `EXPOSE` for `app_port`). `index.html` only gives `sdk: static`.
Body: what the demo does, how to use it (inputs → outputs), the model(s) behind it, limitations, credits and links (GitHub, paper).

## Badges and links between GitHub and the Hub
- In the GitHub README, use `[![Model on HF](https://huggingface.co/datasets/huggingface/badges/resolve/main/model-on-hf-md.svg)](https://huggingface.co/OWNER/NAME)` (also `dataset-on-hf-md.svg`, `open-in-hf-spaces-md.svg`; `-dark` variants exist).
- In the HF card, link to the GitHub repo in "Model sources".
- Use the same pitch, license and numbers in both.
