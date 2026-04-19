#!/bin/bash
cd "$(dirname "$0")"

# 清掉 anaconda base 环境污染的 Qt 相关变量
# 否则 PySide6 的 Qt6 会去 anaconda 的 Qt5 目录找 cocoa plugin 而找不到
unset QT_PLUGIN_PATH
unset QT_QPA_PLATFORM_PLUGIN_PATH
unset DYLD_LIBRARY_PATH
unset DYLD_FRAMEWORK_PATH

exec ./.venv/bin/python main.py
