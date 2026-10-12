<!-- readme-forge template: ML / research code. Replace {{…}}; numbers must be real. Delete sections with no content. -->
<!-- Design pass: swap the title block for templates/design/header-centered.md (generated banner) when the project wants a visual header. -->
<a id="top"></a>
<div align="center">

# {{NAME}}

**{{ONE_SENTENCE_PITCH}}**

[![arXiv](https://img.shields.io/badge/arXiv-{{ARXIV_ID}}-b31b1b)](https://arxiv.org/abs/{{ARXIV_ID}})
[![Model on Hugging Face](https://huggingface.co/datasets/huggingface/badges/resolve/main/model-on-hf-md.svg)](https://huggingface.co/{{HF_MODEL_ID}})
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{{OWNER}}/{{REPO}}/blob/main/{{NOTEBOOK}})
[![License: {{LICENSE}}]({{LICENSE_BADGE_URL}})](LICENSE)

</div>

<img alt="{{teaser figure: what it shows}}" src="{{TEASER_FIGURE}}" width="100%">

## Results

| Model | Params | {{DATASET}} {{METRIC}} ↑ | {{DATASET2}} {{METRIC2}} ↑ |
|---|---|---|---|
| {{BASELINE}} | {{…}} | {{…}} | {{…}} |
| **{{OURS}}** | {{…}} | **{{…}}** | **{{…}}** |

<sub>Evaluated on {{HARDWARE}} with {{SETTINGS}}. Reproduce with `{{EVAL_COMMAND}}`.</sub>

## Quick inference

```python
{{INFERENCE_SNIPPET}}
```

## Installation

```bash
git clone {{REPO_URL}}
cd {{REPO_DIR}}
{{ENV_SETUP}}   # Python {{PY_VERSION}}, CUDA {{CUDA_VERSION}}
```

## Data

{{HOW_TO_DOWNLOAD_AND_PREPARE_DATA}}

## Training

```bash
{{TRAIN_COMMAND}}
```

Takes ~{{HOURS}} h on {{HARDWARE}}. Configs live in `{{CONFIG_DIR}}`.

## Evaluation

```bash
{{EVAL_COMMAND}}
```

## Pretrained checkpoints

| Checkpoint | Params | {{METRIC}} | Download |
|---|---|---|---|
| {{NAME}} | {{…}} | {{…}} | [🤗 Hub](https://huggingface.co/{{HF_MODEL_ID}}) |

## Pipeline

```mermaid
flowchart LR
    {{DATA}} --> {{PREPROCESS}} --> {{TRAIN}} --> {{EVAL}} --> {{EXPORT}}
```

## Project structure

```text
{{TRIMMED_TREE}}
```

## Citation

```bibtex
{{BIBTEX}}
```

## Acknowledgments

{{CODE_DATASETS_AND_COMPUTE_CREDITS}}

## License

Code: [{{LICENSE}}](LICENSE). Model weights: {{WEIGHTS_LICENSE}}.

---

<p align="center"><sub>Released under the <a href="{{LICENSE_FILE}}">{{LICENSE}} License</a> · Built by <a href="{{AUTHOR_URL}}">{{AUTHOR}}</a></sub></p>

<p align="right"><a href="#top">Back to top ↑</a></p>
