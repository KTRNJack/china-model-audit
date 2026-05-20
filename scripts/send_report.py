#!/usr/bin/env python3
"""把最新報告傳送到 Telegram"""
import glob
import requests
from pathlib import Path

TOKEN   = "REMOVED_TOKEN"
CHAT_ID = "5061230259"
RESULTS = Path("/mnt/d/censorship-probe/results")


def send_document(path: Path):
    with open(path, "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendDocument",
            data={"chat_id": CHAT_ID, "caption": "🔍 中國模型審查比較報告"},
            files={"document": (path.name, f, "text/markdown")},
            timeout=30,
        )
    return r.ok


def send_text(text: str):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000], "parse_mode": "Markdown"},
            timeout=15,
        )


def main():
    reports = sorted(RESULTS.glob("report_*.md"))
    if not reports:
        print("找不到報告")
        return
    latest = reports[-1]
    print(f"傳送：{latest}")

    # 先傳文件
    ok = send_document(latest)
    print(f"文件傳送：{'OK' if ok else 'FAILED'}")

    # 再傳摘要
    content = latest.read_text(encoding="utf-8")
    # 只取統計那段
    lines = content.splitlines()
    summary_lines = []
    for line in lines:
        summary_lines.append(line)
        if line.startswith("## 詳細結果"):
            break
    send_text("\n".join(summary_lines))
    print("摘要傳送完成")


if __name__ == "__main__":
    main()
