#!/bin/bash
cd "$(dirname "$0")"

echo "==== PySide6 minimal hello world ===="
export QT_DEBUG_PLUGINS=1
export QT_QPA_PLATFORM_PLUGIN_PATH="$(pwd)/.venv/lib/python3.12/site-packages/PySide6/Qt/plugins/platforms"

./.venv/bin/python - <<'PY'
import sys, os
print("sys.executable:", sys.executable)
print("sys.prefix:", sys.prefix)
print("QT_QPA_PLATFORM_PLUGIN_PATH:", os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH"))
from PySide6.QtWidgets import QApplication, QLabel
app = QApplication(sys.argv)
w = QLabel("HELLO PYSIDE6")
w.resize(400, 200)
w.show()
print("about to enter event loop")
app.exec()
PY

echo "==== exit code: $? ===="
