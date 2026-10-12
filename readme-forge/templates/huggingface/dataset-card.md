---
# readme-forge HF dataset card. Keep only keys you can fill truthfully. See references/huggingface.md.
pretty_name: {{PRETTY_NAME}}
license: {{LICENSE_ID}}
language:
  - {{LANG_CODE}}
task_categories:
  - {{TASK_CATEGORY}}
size_categories:
  - {{SIZE_CATEGORY}}
tags:
  - {{TAG}}
configs:
  - config_name: default
    data_files:
      - split: train
        path: {{TRAIN_GLOB}}
      - split: test
        path: {{TEST_GLOB}}
---

# {{PRETTY_NAME}}

{{ONE_PARAGRAPH_SUMMARY: what's in it, how big, how it was made, what it's for}}

## Quick start

```python
from datasets import load_dataset

ds = load_dataset("{{OWNER}}/{{NAME}}")
print(ds["train"][0])
```

## Dataset structure

### Example instance

```json
{{ONE_REAL_ROW}}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `{{field}}` | `{{string/int/list}}` | {{…}} |

### Splits

| Split | Rows |
|---|---|
| train | {{N}} |
| test | {{N}} |

## Dataset creation

### Curation rationale

{{WHY THIS DATASET EXISTS}}

### Source data

{{WHERE THE RAW DATA CAME FROM; COLLECTION AND FILTERING}}

### Annotations

{{WHO ANNOTATED, GUIDELINES, AGREEMENT}}

### Personal and sensitive information

{{PII PRESENT? HOW HANDLED?}}

## Considerations

### Bias, risks, and limitations

{{…}}

### Intended and out-of-scope uses

{{…}}

## License

{{LICENSE}}. {{SOURCE LICENSE NOTES}}

## Citation

```bibtex
{{BIBTEX}}
```
