<!-- readme-forge profile: data / ML / AI. Replace {{…}}; numbers and links must be real. -->
<!-- Design pass: open with templates/design/header-profile.md (generated hero banner in the user's accent colour) and close with templates/design/footer-svg.md (--style wave). -->
## Hi, I'm {{NAME}}: {{ROLE}}

{{ONE_LINE_RESEARCH_OR_WORK_FOCUS}}

[![Hugging Face: {{HF_USER}}](https://img.shields.io/badge/🤗-{{HF_USER}}-FFD21E?style=flat-square)](https://huggingface.co/{{HF_USER}})
[![Kaggle: {{KAGGLE_USER}}](https://img.shields.io/badge/Kaggle-{{KAGGLE_USER}}-20BEFF?style=flat-square&logo=kaggle&logoColor=white)](https://kaggle.com/{{KAGGLE_USER}})
[![Google Scholar: {{NAME}}](https://img.shields.io/badge/Scholar-{{NAME_URLENC}}-4285F4?style=flat-square&logo=googlescholar&logoColor=white)]({{SCHOLAR_URL}})
[![LinkedIn: {{NAME}}](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square)]({{LINKEDIN_URL}})

### Focus areas

- **{{AREA_1}}**: {{one line, e.g. "parameter-efficient fine-tuning for low-resource languages"}}
- **{{AREA_2}}**: {{…}}
- Currently: {{CURRENT_WORK}}

### Models & datasets

| Name | Type | Highlight |
|---|---|---|
| [{{MODEL}}](https://huggingface.co/{{HF_USER}}/{{MODEL}}) | Model | {{metric on dataset}} |
| [{{DATASET}}](https://huggingface.co/datasets/{{HF_USER}}/{{DATASET}}) | Dataset | {{size, task}} |

### Selected projects

| Project | Summary | Links |
|---|---|---|
| [{{PROJECT}}](https://github.com/{{USER}}/{{PROJECT}}) | {{problem → approach → result}} | [paper]({{…}}) · [demo]({{…}}) |

### Publications

- {{AUTHORS}}. **{{TITLE}}**. *{{VENUE}} {{YEAR}}*. [[paper]]({{URL}}) [[code]]({{URL}})

### Toolbox

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://skillicons.dev/icons?i={{SKILL_IDS}}&theme=dark">
  <img alt="Tools: {{SKILLS_HUMAN_LIST}}" src="https://skillicons.dev/icons?i={{SKILL_IDS}}&theme=light">
</picture>

<!-- skill-icons has py, pytorch, tensorflow, sklearn, opencv, r, julia(?), docker, aws, gcp. For Hugging Face / pandas / JAX use shields badges with logo=huggingface|pandas. -->
