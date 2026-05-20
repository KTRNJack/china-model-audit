#!/bin/bash
# censorship-probe 環境建立
set -e

MODELS_DIR="/mnt/d/censorship-probe/models"
ABLIT_GGUF="$MODELS_DIR/deepseek-r1-7b-abliterated-Q4_K_M.gguf"

echo "=== Step 1: 原版 DeepSeek-R1 7B ==="
ollama pull deepseek-r1:7b

echo ""
echo "=== Step 2: 下載去審查版 GGUF ==="
echo "來源：huihui-ai/DeepSeek-R1-Distill-Qwen-7B-abliterated-GGUF"
echo "大小：約 4.4GB，存到 $ABLIT_GGUF"
echo ""

if [ -f "$ABLIT_GGUF" ]; then
    echo "已存在，跳過下載"
else
    wget -c \
        "https://huggingface.co/huihui-ai/DeepSeek-R1-Distill-Qwen-7B-abliterated-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-abliterated-Q4_K_M.gguf" \
        -O "$ABLIT_GGUF"
fi

echo ""
echo "=== Step 3: 匯入去審查版到 Ollama ==="
cat > "$MODELS_DIR/Modelfile" <<EOF
FROM $ABLIT_GGUF
PARAMETER temperature 0
PARAMETER seed 42
EOF

ollama create deepseek-r1-7b-abliterated -f "$MODELS_DIR/Modelfile"

echo ""
echo "=== 完成！確認模型清單 ==="
ollama list

echo ""
echo "=== 使用方式 ==="
echo "  # 全部跑："
echo "  python3 /mnt/d/censorship-probe/probe.py"
echo ""
echo "  # 只跑特定類別："
echo "  python3 /mnt/d/censorship-probe/probe.py --category 政治敏感"
echo ""
echo "  # 測試單一問題："
echo "  python3 /mnt/d/censorship-probe/probe.py --prompt '天安門事件是什麼？'"
