#!/usr/bin/env python3
"""
update_data.py — 把 data/*.json 合併轉換成 data/all_data.js（給前端用）
跑完新的 probe 後執行一次即可，不需要 HTTP server。

用法：python3 scripts/update_data.py

資料來源：自動掃描 data/*.json，依 type 欄位分類：
  type == "word_probe"  → words（詞彙觸發）
  其餘有 results + models → semantic（語意測試）
"""
import json
from datetime import datetime
from pathlib import Path

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

# ── 模型顯示設定（加新 LLM 只需在這裡加一筆）─────────────────────────────
MODEL_META = {
    "deepseek-r1:7b": {
        "role":    "censored",
        "pair":    "deepseek-r1-7b-abliterated",
        "name":    "DeepSeek-R1 7B",
        "company": "深度求索",
        "dot":     "#818cf8",
    },
    "deepseek-r1:14b": {
        "role":    "censored",
        "pair":    "huihui_ai/deepseek-r1-abliterated:14b",
        "name":    "DeepSeek-R1 14B",
        "company": "深度求索",
        "dot":     "#6366f1",
    },
    "deepseek-r1-7b-abliterated": {
        "role":    "abliterated",
        "name":    "DeepSeek-R1 7B 去審查",
        "company": "深度求索",
        "dot":     "#34d399",
    },
    "huihui_ai/deepseek-r1-abliterated:14b": {
        "role":    "abliterated",
        "name":    "DeepSeek-R1 14B 去審查",
        "company": "深度求索",
        "dot":     "#4ade80",
    },
    "llama3.1:8b": {
        "role":    "neutral",
        "name":    "Llama 3.1 8B",
        "company": "Meta",
        "dot":     "#94a3b8",
    },
    "gemini": {
        "role":    "neutral",
        "name":    "Gemini",
        "company": "Google",
        "dot":     "#4285f4",
    },
    "qwen2.5:7b": {
        "role":    "censored",
        "pair":    "huihui_ai/qwen2.5-abliterate:7b-instruct",
        "name":    "Qwen 2.5 7B",
        "company": "阿里巴巴",
        "dot":     "#f59e0b",
    },
    "huihui_ai/qwen2.5-abliterate:7b-instruct": {
        "role":    "abliterated",
        "name":    "Qwen 2.5 7B 去審查",
        "company": "阿里巴巴",
        "dot":     "#fcd34d",
    },
    "qwen2.5:14b": {
        "role":    "censored",
        "pair":    "huihui_ai/qwen2.5-abliterate:14b-instruct",
        "name":    "Qwen 2.5 14B",
        "company": "阿里巴巴",
        "dot":     "#f97316",
    },
    "huihui_ai/qwen2.5-abliterate:14b-instruct": {
        "role":    "abliterated",
        "name":    "Qwen 2.5 14B 去審查",
        "company": "阿里巴巴",
        "dot":     "#fbbf24",
    },
}


def auto_sources(data_dir: Path) -> list[tuple[str, Path]]:
    """自動掃描 data/*.json，回傳 [(src_key, path), ...]，依檔名排序。"""
    sources = []
    for f in sorted(data_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("type") == "word_probe" and "results" in d:
            sources.append(("words", f))
        elif d.get("type") == "gemini_neutral" and "results" in d:
            pass  # 由 load_gemini_neutral() 單獨處理
        elif "results" in d and "models" in d:
            sources.append(("semantic", f))
    return sources


def load_gemini_neutral(data_dir: Path) -> dict[tuple, dict]:
    """載入最新一份 neutral_gemini_*.json，回傳 {(question, _src): response_dict}。"""
    files = sorted(data_dir.glob("neutral_gemini_*.json"))
    if not files:
        return {}
    latest = files[-1]
    d = json.loads(latest.read_text(encoding="utf-8"))
    cache = {}
    for r in d.get("results", []):
        src = "words" if r.get("src") == "word" else "semantic"
        key = (r["question"], src)
        cache[key] = {"response": r.get("response", ""), "thinking": "", "label": r.get("label", "ANSWERED")}
    print(f"  ✓ [gemini  ] {latest.name}  {len(cache)} 筆")
    return cache


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
    all_results = []
    used_models = set()

    sources = auto_sources(DATA_DIR)
    for src_key, path in sources:
        data = json.loads(path.read_text(encoding="utf-8"))
        file_models = data.get("models", {})
        used_models.update(m for m in file_models.values() if m)

        converted = [convert_result(r, file_models, src_key) for r in data.get("results", [])]
        all_results.extend(converted)
        print(f"  ✓ [{src_key:8}] {path.name}  {len(converted)} 筆")

    gemini_cache = load_gemini_neutral(DATA_DIR)

    # 把同一題（question + category + _src 相同）的多筆合併成一筆
    seen: dict[tuple, int] = {}
    merged: list[dict] = []
    for r in all_results:
        key = (r["question"], r.get("category", ""), r["_src"])
        if key in seen:
            merged[seen[key]]["responses"].update(r["responses"])
            merged[seen[key]]["censored"].update(r["censored"])
        else:
            seen[key] = len(merged)
            merged.append(r)
    all_results = merged

    # 注入 Gemini neutral 回應
    injected = 0
    for r in all_results:
        key = (r["question"], r["_src"])
        if key in gemini_cache:
            r["responses"]["gemini"] = gemini_cache[key]
            injected += 1
    if gemini_cache:
        used_models.add("gemini")
        print(f"  Gemini 注入：{injected} 筆")

    print(f"\n  合併後：{len(all_results)} 筆")

    # 有 Gemini 就用 Gemini 當中立，移除 Llama
    if "gemini" in used_models:
        used_models.discard("llama3.1:8b")

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
