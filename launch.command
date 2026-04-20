#!/bin/bash
cd "$(dirname "$0")"

echo "[sync] 同步 GitHub 最新代码..."
git pull origin main --quiet && echo "[sync] 已是最新" || echo "[sync] 同步失败，使用本地版本"

.venv/bin/python main.py &
SERVER_PID=$!
sleep 1.5
open http://localhost:8765

# 等待服务器退出
wait $SERVER_PID

# 应用关闭后自动保存改动
echo "[save] 检查是否有改动..."
if ! git diff --quiet || ! git diff --cached --quiet; then
    git add .
    git commit -m "auto: $(date '+%Y-%m-%d %H:%M')"
    echo "[save] 已保存并同步到 GitHub"
else
    echo "[save] 无改动，跳过"
fi
