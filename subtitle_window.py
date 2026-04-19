from PySide6.QtCore import Qt, Signal, QTimer, QFileSystemWatcher
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

BG  = "rgb(20, 20, 30)"
BG2 = "rgb(28, 28, 42)"

SCROLL_STYLE = (
    f"QScrollArea {{ border: none; background-color: {BG2}; }}"
    "QScrollBar:vertical { background: rgb(40,40,55); width: 6px; }"
    "QScrollBar::handle:vertical { background: rgb(100,100,130); border-radius: 3px; }"
    "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
)


def _make_scroll(bg: str = BG2):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet(SCROLL_STYLE)
    inner = QWidget()
    inner.setStyleSheet(f"background-color: {bg};")
    layout = QVBoxLayout(inner)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    scroll.setWidget(inner)
    return scroll, layout


class SubtitleWindow(QWidget):
    partial_signal = Signal(str)
    final_signal   = Signal(str)
    start_signal   = Signal()
    ask_signal     = Signal()
    claude_signal  = Signal(str)

    def __init__(
        self,
        font_size: int = 16,
        opacity: float = 0.85,
        w: int = 1100,
        h: int = 420,
        max_lines: int = 800,
    ):
        super().__init__()
        self.max_lines   = max_lines
        self._lines: list[QLabel] = []
        self._claude_lines: list[QLabel] = []
        self._font_size  = font_size
        self._drag_pos   = None
        self._auto_scroll        = True
        self._claude_auto_scroll = True

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(20, 20, 30))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setWindowTitle("会议字幕")
        self.resize(w, h)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - w) // 2, screen.height() - h - 80)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        self.container = QFrame()
        self.container.setStyleSheet(f"QFrame {{ background-color: {BG2}; border-radius: 10px; }}")
        root.addWidget(self.container)

        cv = QVBoxLayout(self.container)
        cv.setContentsMargins(14, 10, 14, 12)
        cv.setSpacing(6)

        # ── 标题栏 ──────────────────────────────────────────
        bar = QHBoxLayout()

        title = QLabel("会议字幕")
        title.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        bar.addWidget(title)
        bar.addStretch(1)

        self._start_btn = QLabel("▶ 启动")
        self._start_btn.setStyleSheet(
            "color: #4caf50; font-weight: bold; padding: 0 10px;"
            "border: 1px solid #4caf50; border-radius: 4px; background: transparent;"
        )
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.mousePressEvent = self._on_start_clicked
        bar.addWidget(self._start_btn)

        self._ask_btn = QLabel("◉ 问 Claude")
        self._ask_btn.setStyleSheet(
            "color: #7eb8f7; font-weight: bold; padding: 0 10px;"
            "border: 1px solid #7eb8f7; border-radius: 4px; background: transparent;"
        )
        self._ask_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ask_btn.mousePressEvent = self._on_ask_clicked
        bar.addWidget(self._ask_btn)

        close_btn = QLabel("✕")
        close_btn.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 0 6px; background: transparent;")
        close_btn.mousePressEvent = lambda _: QApplication.quit()
        bar.addWidget(close_btn)
        cv.addLayout(bar)

        # ── 左右主体 ─────────────────────────────────────────
        body = QHBoxLayout()
        body.setSpacing(0)
        cv.addLayout(body, 1)

        # 左列：字幕
        left = QVBoxLayout()
        left.setSpacing(4)
        left.setContentsMargins(0, 0, 8, 0)

        left_hdr = QLabel("实时字幕")
        left_hdr.setStyleSheet("color: #aaa; font-size: 11px; background: transparent;")
        left.addWidget(left_hdr)

        self.scroll, self.inner_layout = _make_scroll()
        self.scroll.verticalScrollBar().valueChanged.connect(self._check_auto_scroll)
        left.addWidget(self.scroll, 1)

        self.partial_label = QLabel("")
        self.partial_label.setWordWrap(True)
        self.partial_label.setStyleSheet(
            f"color: #ffd966; padding: 4px; background-color: {BG2};"
            f'font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Arial Unicode MS", sans-serif;'
            f"font-size: {font_size}px;"
        )
        left.addWidget(self.partial_label)

        body.addLayout(left, 3)

        # 分割线
        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: rgb(60, 60, 80);")
        body.addWidget(divider)

        # 右列：Claude 回答
        right = QVBoxLayout()
        right.setSpacing(4)
        right.setContentsMargins(8, 0, 0, 0)

        right_hdr = QLabel("Claude 回答")
        right_hdr.setStyleSheet("color: #7eb8f7; font-size: 11px; background: transparent;")
        right.addWidget(right_hdr)

        self.claude_box = QTextEdit()
        self.claude_box.setReadOnly(True)
        self.claude_box.setStyleSheet(
            f"QTextEdit {{ background-color: {BG2}; color: #7eb8f7; border: none; padding: 4px;"
            f'font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Arial Unicode MS", sans-serif;'
            f"font-size: {font_size}px; }}"
        )
        right.addWidget(self.claude_box, 1)

        body.addLayout(right, 2)

        # ── 信号连接 ─────────────────────────────────────────
        self._log_watcher = QFileSystemWatcher()
        self._log_pos = 0

        self.partial_signal.connect(self._on_partial)
        self.final_signal.connect(self._on_final)
        self.claude_signal.connect(self._on_claude)

    # ── log 监视 ──────────────────────────────────────────────
    def set_log_path(self, path: str):
        self._log_pos  = 0
        self._log_path = path
        self._log_watcher.addPath(path)
        self._log_watcher.fileChanged.connect(self._on_log_changed)

    def _on_log_changed(self, _):
        pass

    # ── 按钮回调 ──────────────────────────────────────────────
    def _on_start_clicked(self, _):
        self._start_btn.setText("● 识别中")
        self._start_btn.setStyleSheet(
            "color: #aaa; padding: 0 10px;"
            "border: 1px solid #555; border-radius: 4px; background: transparent;"
        )
        self._start_btn.mousePressEvent = lambda _: None
        self.start_signal.emit()

    def _on_ask_clicked(self, _):
        self._ask_btn.setText("◉ 等待回答…")
        self._ask_btn.setStyleSheet(
            "color: #aaa; padding: 0 10px;"
            "border: 1px solid #555; border-radius: 4px; background: transparent;"
        )
        self.ask_signal.emit()

    # ── 滚动控制 ──────────────────────────────────────────────
    def _check_auto_scroll(self, value: int):
        bar = self.scroll.verticalScrollBar()
        self._auto_scroll = value >= bar.maximum() - 20

    def _scroll_to_bottom(self, scroll):
        QTimer.singleShot(10, lambda: scroll.verticalScrollBar().setValue(
            scroll.verticalScrollBar().maximum()))

    # ── 内容更新 ──────────────────────────────────────────────
    def _on_partial(self, text: str):
        self.partial_label.setText(text)

    def _on_final(self, text: str):
        text = text.strip()
        if not text:
            return
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color: white; padding: 3px 2px; background-color: {BG2};"
            f'font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Arial Unicode MS", sans-serif;'
            f"font-size: {self._font_size}px;"
        )
        self.inner_layout.addWidget(lbl)
        self._lines.append(lbl)

        while len(self._lines) > self.max_lines:
            old = self._lines.pop(0)
            self.inner_layout.removeWidget(old)
            old.deleteLater()

        self.partial_label.setText("")
        if self._auto_scroll:
            self._scroll_to_bottom(self.scroll)

    def _on_claude(self, text: str):
        self._ask_btn.setText("◉ 问 Claude")
        self._ask_btn.setStyleSheet(
            "color: #7eb8f7; font-weight: bold; padding: 0 10px;"
            "border: 1px solid #7eb8f7; border-radius: 4px; background: transparent;"
        )
        self._ask_btn.mousePressEvent = self._on_ask_clicked

        existing = self.claude_box.toPlainText().strip()
        self.claude_box.setPlainText((existing + "\n\n" + text).strip())
        self.claude_box.verticalScrollBar().setValue(
            self.claude_box.verticalScrollBar().maximum()
        )

    # ── 拖动 ─────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
