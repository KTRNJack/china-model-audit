#!/usr/bin/env bash
# full_probe.sh — 一次跑完語意 + 詞彙，完成後自動更新 all_data.js
#
# 用法：
#   bash scripts/full_probe.sh \
#     --orig  "qwen2.5:14b" \
#     --ablit "huihui_ai/qwen2.5-abliterate:14b-instruct" \
#     --label "qwen14b"
#
# 選用參數：
#   --neutral  中立參照模型（預設 llama3.1:8b）
#   --label    檔名標籤
#   --skip-semantic   跳過語意測試
#   --skip-words      跳過詞彙測試

set -euo pipefail
cd "$(dirname "$0")/.."

ORIG=""; ABLIT=""; NEUTRAL="llama3.1:8b"; LABEL=""; SKIP_SEM=0; SKIP_WORDS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --orig)    ORIG="$2";    shift 2 ;;
    --ablit)   ABLIT="$2";   shift 2 ;;
    --neutral) NEUTRAL="$2"; shift 2 ;;
    --label)   LABEL="$2";   shift 2 ;;
    --skip-semantic) SKIP_SEM=1;   shift ;;
    --skip-words)    SKIP_WORDS=1; shift ;;
    *) echo "未知參數: $1"; exit 1 ;;
  esac
done

if [[ -z "$ORIG" || -z "$ABLIT" ]]; then
  echo "用法: bash scripts/full_probe.sh --orig MODEL --ablit MODEL [--label LABEL]"
  exit 1
fi

LABEL_ARG=${LABEL:+--label "$LABEL"}
echo "======================================================"
echo "  模型：$ORIG"
echo "  去審查：$ABLIT"
echo "  中立：$NEUTRAL"
echo "======================================================"

if [[ $SKIP_SEM -eq 0 ]]; then
  echo ""
  echo "▶ 語意測試（42 題）..."
  python3 scripts/probe.py \
    --orig    "$ORIG" \
    --ablit   "$ABLIT" \
    --neutral "$NEUTRAL" \
    ${LABEL_ARG:-}
fi

if [[ $SKIP_WORDS -eq 0 ]]; then
  echo ""
  echo "▶ 詞彙觸發測試（147 題）..."
  python3 scripts/word_probe.py \
    --orig  "$ORIG" \
    --ablit "$ABLIT"
fi

echo ""
echo "▶ 更新 data/all_data.js ..."
python3 scripts/update_data.py

echo ""
echo "✅ 全部完成！"
