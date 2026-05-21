#!/usr/bin/env python3
"""
gemini_neutral.py — 用 Gemini CLI 對所有已測試題目問一次中立回應，
                    結果存入 data/neutral_gemini_YYYY-MM-DD.json。

之後 update_data.py 會自動把 Gemini 的回應當作 neutral 注入所有題目。

用法：
  python3 scripts/gemini_neutral.py              # 全部跑
  python3 scripts/gemini_neutral.py --retry-only # 只補跑 NEEDS_RETRY 的題目
"""
import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOT       = Path(__file__).parent.parent
DATA_DIR   = ROOT / "data"
DELAY      = 2    # 每題之間等幾秒，避免 Gemini rate limit
TIMEOUT    = 120  # 單題最長等幾秒

REFUSE_HEAD = [
    "i'm unable", "i cannot", "i can't", "i won't", "as a software engineering",
    "我無法", "無法回答", "不予回答", "設計目的是協助軟體",
    "cannot execute local shell", "i will begin by examining",
    "i will now run",
]


def ask_gemini(question: str) -> str:
    try:
        r = subprocess.run(
            ["gemini", "--skip-trust", "-p", question],
            capture_output=True, text=True, timeout=TIMEOUT,
            cwd="/tmp",  # 中立目錄，避免 Gemini CLI 讀取專案上下文
            env={"HOME": "/home/jack", "PATH": "/home/jack/.nvm/versions/node/v24.14.0/bin:/usr/bin:/bin",
                 "GEMINI_CLI_TRUST_WORKSPACE": "true"},
        )
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[GEMINI_TIMEOUT]"
    except Exception as e:
        return f"[GEMINI_ERROR: {e}]"


def label_response(response: str) -> str:
    if response.startswith("[GEMINI"):
        return "ERROR"
    head = response[:150].lower()
    if any(w in head for w in REFUSE_HEAD) or len(response) < 30:
        return "REFUSED"
    return "ANSWERED"


def collect_questions(data_dir: Path) -> list[dict]:
    seen = set()
    questions = []
    for f in sorted(data_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("type") in ("gemini_neutral", "word_probe"):
            is_word = d.get("type") == "word_probe"
        elif "models" in d and "results" in d:
            is_word = False
        else:
            continue
        src = "word" if is_word else "semantic"
        for r in d.get("results", []):
            q = r.get("question", "")
            if not q:
                continue
            key = (q, src)
            if key in seen:
                continue
            seen.add(key)
            questions.append({
                "question":   q,
                "category":   r.get("category", ""),
                "src":        src,
                "probe_type": r.get("probe_type", ""),
            })
    return questions


def get_retry_questions(data_dir: Path) -> set[str]:
    """回傳所有標記為 NEEDS_RETRY 的題目。"""
    retry = set()
    for f in sorted(data_dir.glob("neutral_gemini_*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for r in d.get("results", []):
            if r.get("label") == "NEEDS_RETRY":
                retry.add(r["question"])
    return retry


def update_existing(data_dir: Path, new_results: list[dict]) -> Path:
    """把新結果更新進最新的 neutral_gemini_*.json，不建新檔。"""
    files = sorted(data_dir.glob("neutral_gemini_*.json"))
    if not files:
        return None
    path = files[-1]
    d = json.loads(path.read_text(encoding="utf-8"))
    by_q = {r["question"]: r for r in d["results"]}
    for nr in new_results:
        if nr["question"] in by_q:
            by_q[nr["question"]].update(nr)
    d["results"] = list(by_q.values())
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry-only", action="store_true", help="只補跑 NEEDS_RETRY 的題目")
    args = parser.parse_args()

    all_questions = collect_questions(DATA_DIR)

    if args.retry_only:
        retry_set = get_retry_questions(DATA_DIR)
        questions = [q for q in all_questions if q["question"] in retry_set]
        print(f"補跑模式：{len(questions)} 題需重跑\n")
    else:
        questions = all_questions
        print(f"共 {len(questions)} 題（semantic: {sum(1 for q in questions if q['src']=='semantic')}，"
              f"word: {sum(1 for q in questions if q['src']=='word')}）\n")

    results = []
    for i, q in enumerate(questions, 1):
        print(f"[{i:3}/{len(questions)}] {q['src']:8} {q['question'][:55]}", end=" ", flush=True)
        response = ask_gemini(q["question"])
        lbl = label_response(response)
        print(f"→ {lbl}")
        results.append({
            "question":   q["question"],
            "category":   q["category"],
            "src":        q["src"],
            "probe_type": q["probe_type"],
            "response":   response,
            "label":      lbl,
        })
        if i < len(questions):
            time.sleep(DELAY)

    if args.retry_only:
        path = update_existing(DATA_DIR, results)
        print(f"\n✅  更新至 {path.name}")
    else:
        out = {
            "type":      "gemini_neutral",
            "model":     "gemini",
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "results":   results,
        }
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        path = DATA_DIR / f"neutral_gemini_{ts}.json"
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    answered = sum(1 for r in results if r["label"] == "ANSWERED")
    refused  = sum(1 for r in results if r["label"] == "REFUSED")
    errors   = sum(1 for r in results if r["label"] in ("ERROR", "NEEDS_RETRY"))
    print(f"    ANSWERED={answered}  REFUSED={refused}  ERROR/RETRY={errors}")
    print(f"    執行 python3 scripts/update_data.py 以更新前端")


if __name__ == "__main__":
    main()
