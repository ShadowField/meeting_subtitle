#!/bin/bash
cd "$(dirname "$0")"

echo "[sync] 同步 GitHub 最新代码..."
git pull origin main --quiet && echo "[sync] 已是最新" || echo "[sync] 同步失败，使用本地版本"

.venv/bin/python main.py &
sleep 1.5
open http://localhost:8765
wait
