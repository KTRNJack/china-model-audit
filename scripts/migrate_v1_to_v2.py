#!/usr/bin/env python3
"""
把 v1 格式的 JSON 資料遷移到 v2 格式：
  - 移除 emoji label → 純字串 REFUSED / DEFLECTED / ANSWERED
  - 從舊 response 中拆出 <think> 內容
  - 移除垃圾資料（category 為空，或非問句的項目）
  - 重新計算 censored 邏輯
  - 同步更新 results/ 和 site/data/
"""
import json
import re
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
SITE_DIR    = Path(__file__).parent / "site" / "data"

LABEL_MAP = {
    "🚫 REFUSED":   "REFUSED",
    "↩️  DEFLECTED": "DEFLECTED",
    "✅ ANSWERED":  "ANSWERED",
    "REFUSED":   "REFUSED",
    "DEFLECTED": "DEFLECTED",
    "ANSWERED":  "ANSWERED",
}

KNOWN_CATEGORIES = {
    "政治敏感", "歷史重寫", "政府批評", "台灣主權", "法輪功",
    "對照組（應正常回答）", "有害內容對照（兩者應皆拒答）",
    "日中關係", "歷史事件", "政治領導人", "民族宗教迫害",
    "台灣香港", "網路新聞審查", "社會運動事件",
}


def extract_thinking(text: str) -> tuple[str, str]:
    m = re.search(r'<think>([\s\S]*?)</think>', text)
    if m:
        thinking = m.group(1).strip()
        response = (text[:m.start()] + text[m.end():]).strip()
        return thinking, response
    return "", text


def normalize_label(label: str) -> str:
    for k, v in LABEL_MAP.items():
        if k in label:
            return v
    return "ANSWERED"


def is_garbage(entry: dict) -> bool:
    cat = entry.get("category", "")
    q   = entry.get("question", "")
    if cat not in KNOWN_CATEGORIES and cat == "":
        return True
    # 明顯不是問句的項目（食譜段落、標題）
    garbage_markers = ["：", "总结", "步骤", "材料", "注意事项", "综合影响", "的影响"]
    if not cat and any(m in q for m in garbage_markers):
        return True
    return False


def migrate_entry(entry: dict) -> dict:
    def fix_side(side: dict) -> dict:
        raw_response = side.get("response", "")
        thinking, response = extract_thinking(raw_response)
        # 如果 thinking 已經是空字串但 response 有 <think> 標籤（舊格式）
        if not thinking and "<think>" not in raw_response:
            thinking = side.get("thinking", "")
        label = normalize_label(side.get("label", "ANSWERED"))
        return {"response": response, "thinking": thinking, "label": label}

    orig  = fix_side(entry.get("original", {}))
    ablit = fix_side(entry.get("abliterated", {}))

    # 重新計算 censored：原版拒答/迴避，且去審查版作答
    censored = orig["label"] in ("REFUSED", "DEFLECTED") and ablit["label"] == "ANSWERED"

    return {
        "question":    entry.get("question", ""),
        "category":    entry.get("category", ""),
        "probe_type":  entry.get("probe_type", ""),
        "original":    orig,
        "abliterated": ablit,
        "censored":    censored,
    }


def migrate_file(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))

    # 已是 v2 格式就跳過
    if data.get("format") == "v2":
        print(f"  已是 v2，跳過：{path.name}")
        return data

    results_raw = data.get("results", [])
    results_clean = []
    removed = 0
    for entry in results_raw:
        if is_garbage(entry):
            removed += 1
            continue
        results_clean.append(migrate_entry(entry))

    data["format"]  = "v2"
    data["results"] = results_clean
    print(f"  {path.name}: {len(results_raw)} → {len(results_clean)} 筆（移除 {removed} 筆垃圾）")
    return data


def main():
    files = list(RESULTS_DIR.glob("*.json")) + list(SITE_DIR.glob("*.json"))
    seen = set()
    for path in files:
        if path.name in seen:
            continue
        seen.add(path.name)
        print(f"處理：{path}")
        data = migrate_file(path)

        # 寫回兩個位置
        for d in [RESULTS_DIR, SITE_DIR]:
            out = d / path.name
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n✅ 遷移完成")


if __name__ == "__main__":
    main()
