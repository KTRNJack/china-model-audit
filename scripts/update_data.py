#!/usr/bin/env python3
"""
update_data.py — 把 data/*.json 合併轉換成 data/all_data.js（給前端用）
跑完新的 probe 後執行一次即可，不需要 HTTP server。

用法：python3 scripts/update_data.py
"""
import json
from datetime import datetime
from pathlib import Path

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

# ── 要納入的資料來源 ───────────────────────────────────────────────────────
# key = 前端過濾用的來源識別碼，path = JSON 檔路徑
SOURCES = [
    ("semantic", DATA_DIR / "data_2026-05-20_23-18_v3_three_way.json"),
    ("words",    DATA_DIR / "words_deepseek-r1-7b_2026-05-20.json"),
    # 之後加新 probe 結果：
    # ("semantic", DATA_DIR / "data_YYYY-MM-DD_qwen.json"),
]

# ── 模型顯示設定（加新 LLM 只需在這裡加一筆）─────────────────────────────
MODEL_META = {
    "deepseek-r1:7b": {
        "role": "censored",
        "pair": "deepseek-r1-7b-abliterated",
        "name": "DeepSeek-R1 7B",
        "dot":  "#818cf8",
    },
    "deepseek-r1-7b-abliterated": {
        "role": "abliterated",
        "name": "DeepSeek-R1 7B 去審查",
        "dot":  "#34d399",
    },
    "llama3.1:8b": {
        "role": "neutral",
        "name": "Llama 3.1 8B",
        "dot":  "#94a3b8",
    },
    # "qwen2.5:7b": {
    #     "role": "censored",
    #     "pair": "qwen2.5-7b-abliterated",
    #     "name": "Qwen 2.5 7B",
    #     "dot":  "#f59e0b",
    # },
    # "qwen2.5-7b-abliterated": {
    #     "role": "abliterated",
    #     "name": "Qwen 2.5 7B 去審查",
    #     "dot":  "#86efac",
    # },
}


def convert_result(r: dict, file_models: dict, src_key: str) -> dict:
    """舊格式（original/neutral/abliterated）→ 新格式（responses by model name）"""
    responses = {}
    for role, model_name in file_models.items():
        if not model_name or role not in r:
            continue
        side = r[role]
        if isinstance(side, dict) and "label" in side:
            responses[model_name] = {
                "response": side.get("response", ""),
                "thinking": side.get("thinking", ""),
                "label":    side["label"],
            }

    # censored flag：每個 censored 模型獨立標記
    censored = {}
    for model_name, info in MODEL_META.items():
        if info["role"] != "censored" or model_name not in responses:
            continue
        pair = info.get("pair", "")
        orig_label  = responses[model_name]["label"]
        ablit_label = responses.get(pair, {}).get("label", "")
        censored[model_name] = orig_label in ("REFUSED", "DEFLECTED") and ablit_label == "ANSWERED"

    out = {
        "question":  r.get("question", ""),
        "category":  r.get("category", ""),
        "_src":      src_key,
        "responses": responses,
        "censored":  censored,
    }
    if r.get("probe_type"):
        out["probe_type"] = r["probe_type"]
    return out


def main():
    all_results  = []
    used_models  = set()

    for src_key, path in SOURCES:
        if not path.exists():
            print(f"⚠  找不到 {path.name}，跳過")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        file_models = data.get("models", {})
        used_models.update(m for m in file_models.values() if m)

        converted = [convert_result(r, file_models, src_key) for r in data.get("results", [])]
        all_results.extend(converted)
        print(f"  ✓ {path.name}  {len(converted)} 筆")

    # META 只納入本次資料實際用到的模型
    models_meta = {
        m: MODEL_META.get(m, {"role": "unknown", "name": m, "dot": "#64748b"})
        for m in used_models
    }
    meta = {"generated": datetime.now().strftime("%Y-%m-%d"), "models": models_meta}

    out_js = "\n".join([
        "/* 自動生成 — 執行 python3 scripts/update_data.py 重新產生 */",
        f"const META = {json.dumps(meta, ensure_ascii=False, indent=2)};",
        f"const DATA = {json.dumps(all_results, ensure_ascii=False)};",
    ])

    out_path = DATA_DIR / "all_data.js"
    out_path.write_text(out_js, encoding="utf-8")

    total    = len(all_results)
    censored = sum(1 for r in all_results if any(r["censored"].values()))
    refused  = sum(
        1 for r in all_results
        if any(
            r["responses"].get(m, {}).get("label") == "REFUSED"
            for m, info in models_meta.items() if info["role"] == "censored"
        )
    )
    print(f"\n✅  data/all_data.js  ({len(out_js)//1024} KB, {total} 筆)")
    print(f"    原版拒答: {refused}  審查確認: {censored}")


if __name__ == "__main__":
    main()
