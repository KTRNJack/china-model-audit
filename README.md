# China Model Audit

Comparing censored vs. abliterated versions of Chinese LLMs to document what gets suppressed.

## How it works

- **Original model**: `deepseek-r1:7b` (with CCP censorship baked in via RLHF)
- **Abliterated model**: same base weights, refusal direction vectors removed
- **Test suite**: 30+ questions across 6 categories (political, historical, Taiwan, HK, etc.)

## Findings

Three tiers of censorship detected:

| Tier | Behavior | Example topics |
|------|----------|---------------|
| Hard block | Both versions refuse | Tiananmen date/casualties, CCP criticism |
| Propaganda replacement | Both "answer" with CCP narrative | Xinjiang, Tibet, Taiwan sovereignty |
| Partial (abliteration works) | Original refuses, abliterated answers | Xi/Mao comparison, HK 2019 |

## Running your own probe

```bash
# Requires Ollama with both models installed
pip install requests
python tools/probe.py                          # all categories
python tools/probe.py --category 政治敏感      # single category
python tools/probe.py --prompt "your question" # single question
```

## Adding new models

1. Add probe result JSON to `data/`
2. Add entry to `DATASETS` array in `index.html`
