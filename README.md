# Meeting Subtitle 会议实时字幕

一个 macOS 桌面工具，捕获系统音频并通过阿里云 NLS 实时语音识别生成中文字幕，字幕以悬浮窗口显示在屏幕上，并可一键向 Claude 提问获取摘要或回答。

![界面示意](https://img.shields.io/badge/platform-macOS-blue) ![Python](https://img.shields.io/badge/python-3.10%2B-green) ![PySide6](https://img.shields.io/badge/GUI-PySide6-orange)

## 功能特性

- **实时字幕**：捕获系统音频，通过阿里云 NLS WebSocket 流式识别，毫秒级延迟显示中文字幕
- **悬浮窗口**：始终置顶、可拖动的半透明字幕窗口，不影响其他应用使用
- **自动滚动**：字幕自动滚动到最新内容，手动上滑后暂停自动滚动
- **问 Claude**：一键将当前字幕内容发送给 Claude，获取摘要或问题解答，回答显示在右侧面板
- **增量提问**：每次点击"问 Claude"只发送上次提问之后的新增字幕，避免重复上下文
- **自动记录**：所有字幕和 Claude 回答自动保存到带时间戳的日志文件

## 界面截图

```
┌─────────────────────────────────────────────────────────┐
│ 会议字幕          ● 识别中    ◉ 问 Claude            ✕ │
├──────────────────────────────┬──────────────────────────┤
│ 实时字幕                     │ Claude 回答              │
│                              │                          │
│ 这是一段实时识别的字幕内容   │ 会议讨论了 XX 话题，     │
│ 语音识别后自动显示在这里     │ 核心结论是...            │
│                              │                          │
│ [实时识别中的黄色预览文字]   │                          │
└──────────────────────────────┴──────────────────────────┘
```

## 系统要求

- macOS 10.15+
- Python 3.10+
- [BlackHole](https://existential.audio/blackhole/)（虚拟音频驱动，用于捕获系统音频）
- 阿里云 NLS 实时语音识别服务账号
- Claude Code CLI（用于"问 Claude"功能）

## 安装步骤

### 1. 安装 BlackHole 虚拟音频驱动

前往 [BlackHole 官网](https://existential.audio/blackhole/) 下载安装 BlackHole 2ch。

安装后在**系统设置 → 声音 → 输出**中创建「多输出设备」，同时勾选 BlackHole 2ch 和你的扬声器/耳机，这样音频既能播放又能被捕获。

### 2. 克隆项目

```bash
git clone https://github.com/ShadowField/meeting_subtitle.git
cd meeting_subtitle
```

### 3. 创建 Python 虚拟环境

> **重要**：如果系统安装了 Anaconda，必须使用 `--copies` 参数，否则 Qt 会被 Anaconda 的配置文件劫持导致无法启动。

```bash
python3 -m venv .venv --copies
source .venv/bin/activate
```

### 4. 安装依赖

```bash
# 安装阿里云 NLS SDK（不在 PyPI，从 GitHub 安装）
pip install --no-deps https://github.com/aliyun/alibabacloud-nls-python-sdk/archive/refs/heads/master.zip

# 安装其他依赖
pip install -r requirements.txt
```

### 5. 配置阿里云凭证

```bash
cp config.ini.example config.ini
```

编辑 `config.ini`，填入你的阿里云信息：

```ini
[aliyun]
access_key_id = 你的 AccessKey ID
access_key_secret = 你的 AccessKey Secret
appkey = 你的语音识别项目 Appkey
region = cn-shanghai
```

阿里云 NLS 服务开通地址：[https://nls-portal.console.aliyun.com](https://nls-portal.console.aliyun.com)

### 6. 启动

```bash
open launch.command
```

或者直接运行：

```bash
source .venv/bin/activate
python main.py
```

## 使用方法

1. 启动后点击窗口中的 **▶ 启动** 按钮开始识别
2. 播放音频或开始说话，字幕会实时出现在左侧
3. 点击 **◉ 问 Claude** 将当前字幕发送给 Claude，回答显示在右侧
4. 窗口可以拖动到屏幕任意位置
5. 日志文件自动保存在 `./logs/` 目录下

## 配置项说明

`config.ini` 支持以下配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `aliyun.access_key_id` | — | 阿里云 AccessKey ID |
| `aliyun.access_key_secret` | — | 阿里云 AccessKey Secret |
| `aliyun.appkey` | — | NLS 项目 Appkey |
| `aliyun.region` | `cn-shanghai` | NLS 服务地域 |
| `ui.window_width` | `820` | 窗口宽度（像素）|
| `ui.window_height` | `420` | 窗口高度（像素）|
| `ui.font_size` | `16` | 字幕字号 |
| `ui.opacity` | `0.85` | 窗口透明度（0~1）|
| `ui.max_history_lines` | `800` | 最大保留字幕行数 |
| `log.save_dir` | `./logs` | 日志保存目录 |

## 项目结构

```
meeting_subtitle/
├── main.py              # 入口，负责初始化和模块串联
├── subtitle_window.py   # Qt 字幕窗口 UI
├── asr_client.py        # 阿里云 NLS WebSocket 客户端
├── audio_capture.py     # 系统音频捕获（loopback）
├── token_manager.py     # 阿里云 Token 获取与缓存
├── logger.py            # 会议日志记录
├── launch.command       # macOS 一键启动脚本
├── config.ini.example   # 配置文件模板
└── requirements.txt     # Python 依赖
```

## 常见问题

**Q: 启动后没有字幕出现**

检查系统音频输出是否设置为「多输出设备」（包含 BlackHole）。可运行 `open audio_test.command` 测试音频捕获是否正常。

**Q: 报错 `Could not load Qt platform plugin "cocoa"`**

不要直接在终端运行 `python main.py`，使用 `open launch.command` 启动，确保在 GUI 会话中运行。

**Q: 安装了 Anaconda 后 Qt 无法启动**

创建 venv 时必须加 `--copies` 参数：`python3 -m venv .venv --copies`

**Q: 问 Claude 功能不可用**

需要安装并登录 [Claude Code CLI](https://claude.ai/code)。确认 `~/.local/lib/nodejs/current/bin/claude` 路径存在。

## 注意事项

- `config.ini` 包含阿里云密钥，已加入 `.gitignore`，请勿提交到代码仓库
- 阿里云 NLS Token 有效期约 24 小时，程序会自动刷新
- NLS WebSocket 会话有约 10 分钟限制，程序会自动重连
- macOS 隐私设置需要授予麦克风权限（即使是捕获系统音频）

## License

MIT
