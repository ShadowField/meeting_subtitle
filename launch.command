#!/bin/bash
cd "$(dirname "$0")"
.venv/bin/python main.py &
sleep 1.5
open http://localhost:8765
wait
