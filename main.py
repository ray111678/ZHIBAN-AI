import sys, os, json, base64, subprocess, traceback
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QLineEdit, QSystemTrayIcon, QMenu, QMessageBox,
    QDialog, QFormLayout, QComboBox, QCheckBox, QListWidget, QListWidgetItem,
    QInputDialog, QFrame
)

APP_NAME = "智伴 AI"
BASE = Path(os.getenv("APPDATA", str(Path.home()))) / "ZhiBanAI"
BASE.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = BASE / "config.json"
TODO_FILE = BASE / "todos.json"

DEFAULTS = {
    "api_base": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4o-mini",
    "system_prompt": "你是智伴 AI，一个可靠、清晰、友好的 Windows 桌面助手。请使用中文回答，除非用户指定其他语言。",
    "speak": False,
    "launch_minimized": False
}

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default.copy() if isinstance(default, dict) else default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

class Worker(QThread):
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, cfg, messages):
        super().__init__()
        self.cfg, self.messages = cfg, messages

    def run(self):
        try:
            import requests
            base = self.cfg["api_base"].strip().rstrip("/")
            if base.endswith("/chat/completions"):
                url = base
            else:
                url = base + "/chat/completions"
            headers = {"Content-Type": "application/json"}
            if self.cfg["api_key"].strip():
                headers["Authorization"] = "Bearer " + self.cfg["api_key"].strip()
            payload = {"model": self.cfg["model"], "messages": self.messages, "temperature": 0.7}
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            self.done.emit(data["choices"][0]["message"]["content"])
        except Exception as e:
            self.failed.emit(f"{e}\n\n请检查 API 地址、密钥、模型名称和网络连接。")

class SettingsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.setWindowTitle("智伴 AI · 设置")
        self.setMinimumWidth(460)
        self.cfg = cfg.copy()
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.base = QLineEdit(cfg["api_base"])
        self.key = QLineEdit(cfg["api_key"]); self.key.setEchoMode(QLineEdit.Password)
        self.model = QLineEdit(cfg["model"])
        self.prompt = QTextEdit(cfg["system_prompt"]); self.prompt.setFixedHeight(90)
        self.speak = QCheckBox("回答完成后朗读（需要语音组件）")
        self.speak.setChecked(bool(cfg.get("speak", False)))
        self.minimized = QCheckBox("启动时最小化到系统托盘")
        self.minimized.setChecked(bool(cfg.get("launch_minimized", False)))
        form.addRow("API Base URL", self.base)
        form.addRow("API Key", self.key)
        form.addRow("模型名称", self.model)
        form.addRow("系统提示词", self.prompt)
        layout.addLayout(form); layout.addWidget(self.speak); layout.addWidget(self.minimized)
        hint = QLabel("支持 OpenAI 兼容的 Chat Completions 接口。密钥仅保存在本机配置目录。")
        hint.setWordWrap(True); hint.setStyleSheet("color:#91a4bd")
        layout.addWidget(hint)
        row = QHBoxLayout()
        save = QPushButton("保存设置"); cancel = QPushButton("取消")
        save.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        row.addStretch(); row.addWidget(cancel); row.addWidget(save); layout.addLayout(row)

    def values(self):
        return {
            "api_base": self.base.text().strip(),
            "api_key": self.key.text().strip(),
            "model": self.model.text().strip(),
            "system_prompt": self.prompt.toPlainText().strip(),
            "speak": self.speak.isChecked(),
            "launch_minimized": self.minimized.isChecked()
        }

class FloatingAssistant(QWidget):
    def __init__(self, show_main):
        super().__init__(None, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.show_main = show_main
        self.setWindowTitle("智伴 AI")
        self.setFixedSize(190, 72)
        self.setStyleSheet("QWidget{background:#101d35;border:1px solid #2c83d8;border-radius:18px;color:white}")
        row = QHBoxLayout(self)
        logo = QLabel("✦"); logo.setStyleSheet("font-size:28px;color:#53c7ff;border:0")
        text = QLabel("智伴 AI\n随时为你服务"); text.setStyleSheet("border:0;font-size:12px")
        btn = QPushButton("打开"); btn.setStyleSheet("background:#1769aa;border:0;padding:8px;border-radius:9px")
        btn.clicked.connect(self.show_main)
        row.addWidget(logo); row.addWidget(text); row.addWidget(btn)
        self.move(40, 140)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = load_json(CONFIG_FILE, DEFAULTS)
        for k, v in DEFAULTS.items(): self.cfg.setdefault(k, v)
        self.history = []
        self.worker = None
        self.setWindowTitle("智伴 AI · Windows 桌面助手")
        self.resize(1040, 720)
        self.setMinimumSize(760, 560)
        self.setStyleSheet("""
            QMainWindow,QWidget{background:#0b1220;color:#e8f1ff;font-family:'Microsoft YaHei UI';}
            QFrame#panel{background:#111d31;border:1px solid #203654;border-radius:14px;}
            QPushButton{background:#1769aa;color:white;border:0;border-radius:9px;padding:9px 14px;}
            QPushButton:hover{background:#2488d1;} QPushButton:disabled{background:#33465e;color:#9aabc0;}
            QLineEdit,QTextEdit,QListWidget{background:#0e192b;border:1px solid #29415f;border-radius:9px;padding:9px;color:#edf5ff;}
            QLabel#muted{color:#91a4bd;} QMenu{background:#14233a;color:white;}
        """)
        self._build_ui()
        self._build_tray()
        self.floating = FloatingAssistant(self.showNormal)
        self.statusBar().showMessage("就绪 · Alt + Space 可唤起窗口（需启用快捷键组件）")
        self.install_hotkey()
        if self.cfg.get("launch_minimized"):
            QTimer.singleShot(300, self.hide)

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        outer = QHBoxLayout(central); outer.setContentsMargins(18,18,18,18); outer.setSpacing(16)
        side = QFrame(); side.setObjectName("panel"); side.setFixedWidth(230)
        sl = QVBoxLayout(side)
        brand = QLabel("✦  智伴 AI"); brand.setStyleSheet("font-size:23px;font-weight:700;color:#65c8ff;padding:8px")
        sl.addWidget(brand)
        desc = QLabel("你的 Windows 智能桌面伙伴"); desc.setObjectName("muted"); sl.addWidget(desc)
        sl.addSpacing(20)
        for label, fn in [("＋ 新建对话", self.new_chat), ("⚙ 设置", self.open_settings),
                          ("▣ 理解当前屏幕", self.capture_screen), ("◉ 悬浮助手", self.toggle_float)]:
            b = QPushButton(label); b.clicked.connect(fn); sl.addWidget(b)
        sl.addSpacing(14)
        sl.addWidget(QLabel("本地待办"))
        self.todo_list = QListWidget(); self.todo_list.setMaximumHeight(190)
        sl.addWidget(self.todo_list)
        todo_row = QHBoxLayout()
        self.todo_input = QLineEdit(); self.todo_input.setPlaceholderText("添加一条待办…")
        add = QPushButton("添加"); add.clicked.connect(self.add_todo)
        todo_row.addWidget(self.todo_input); todo_row.addWidget(add); sl.addLayout(todo_row)
        remove = QPushButton("删除选中待办"); remove.clicked.connect(self.remove_todo); sl.addWidget(remove)
        sl.addStretch()
        note = QLabel("隐私提示：屏幕截图仅在你主动点击并确认后发送。")
        note.setWordWrap(True); note.setObjectName("muted"); sl.addWidget(note)
        outer.addWidget(side)
        right = QFrame(); right.setObjectName("panel"); rl = QVBoxLayout(right); rl.setContentsMargins(18,18,18,18)
        top = QHBoxLayout()
        title = QLabel("智能对话"); title.setStyleSheet("font-size:20px;font-weight:700")
        self.api_state = QLabel("未配置 API"); self.api_state.setObjectName("muted")
        top.addWidget(title); top.addStretch(); top.addWidget(self.api_state); rl.addLayout(top)
        self.chat = QTextEdit(); self.chat.setReadOnly(True)
        self.chat.setPlaceholderText("你好！我是智伴 AI。配置 API 后，就可以开始对话。")
        rl.addWidget(self.chat, 1)
        self.input = QTextEdit(); self.input.setFixedHeight(100); self.input.setPlaceholderText("输入消息…（Ctrl + Enter 发送）")
        rl.addWidget(self.input)
        actions = QHBoxLayout()
        self.send_btn = QPushButton("发送  ➤"); self.send_btn.clicked.connect(self.send_message)
        self.clear_btn = QPushButton("清空对话"); self.clear_btn.clicked.connect(self.new_chat)
        actions.addWidget(self.clear_btn); actions.addStretch(); actions.addWidget(self.send_btn)
        rl.addLayout(actions); outer.addWidget(right, 1)
        self.refresh_todos()
        self.api_state.setText("API 已配置" if self.cfg["api_key"] else "请先配置 API")

    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        menu = QMenu()
        menu.addAction("打开智伴 AI", self.showNormal)
        menu.addAction("显示/隐藏悬浮助手", self.toggle_float)
        menu.addSeparator(); menu.addAction("退出", QApplication.quit)
        self.tray.setContextMenu(menu); self.tray.activated.connect(lambda reason: self.showNormal() if reason == QSystemTrayIcon.DoubleClick else None)
        self.tray.show()

    def install_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey("alt+space", lambda: QTimer.singleShot(0, self.showNormal), suppress=False)
            self.hotkey_ok = True
        except Exception:
            self.hotkey_ok = False
            self.statusBar().showMessage("全局快捷键不可用；可通过系统托盘打开。")

    def append(self, who, text):
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        color = "#63c7ff" if who == "你" else "#a9e6bd"
        self.chat.append(f'<p style="margin:12px 0 4px;color:{color};font-weight:bold">{who}</p><p style="margin:0 0 12px">{safe}</p>')

    def send_message(self):
        text = self.input.toPlainText().strip()
        if not text or (self.worker and self.worker.isRunning()): return
        if not self.cfg["api_key"]:
            QMessageBox.information(self, "需要配置 API", "请先点击左侧“设置”，填写兼容接口地址、API Key 和模型名称。")
            self.open_settings(); return
        self.input.clear(); self.append("你", text)
        self.history.append({"role":"user","content":text})
        messages = [{"role":"system","content":self.cfg["system_prompt"]}] + self.history[-30:]
        self.send_btn.setEnabled(False); self.send_btn.setText("思考中…")
        self.worker = Worker(self.cfg, messages)
        self.worker.done.connect(self.on_reply); self.worker.failed.connect(self.on_error); self.worker.start()

    def on_reply(self, answer):
        self.history.append({"role":"assistant","content":answer})
        self.append("智伴 AI", answer)
        self.send_btn.setEnabled(True); self.send_btn.setText("发送  ➤")
        if self.cfg.get("speak"):
            try:
                import pyttsx3
                engine = pyttsx3.init(); engine.say(answer[:1200]); engine.runAndWait()
            except Exception: pass

    def on_error(self, error):
        self.append("系统提示", error)
        self.send_btn.setEnabled(True); self.send_btn.setText("发送  ➤")

    def new_chat(self):
        self.history = []; self.chat.clear()

    def open_settings(self):
        dlg = SettingsDialog(self.cfg, self)
        if dlg.exec():
            self.cfg.update(dlg.values()); save_json(CONFIG_FILE, self.cfg)
            self.api_state.setText("API 已配置" if self.cfg["api_key"] else "请先配置 API")
            self.statusBar().showMessage("设置已保存到本机。", 4000)

    def capture_screen(self):
        answer = QMessageBox.question(self, "屏幕理解确认",
            "即将截取当前屏幕，并发送给你配置的模型服务商进行分析。\n请先关闭不希望分享的窗口或敏感信息。\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes: return
        if not self.cfg["api_key"]:
            QMessageBox.information(self, "尚未配置 API", "请先在设置中配置 API。"); return
        try:
            import pyautogui
            from PySide6.QtWidgets import QFileDialog
            img = pyautogui.screenshot()
            path = BASE / "last_screen_capture.png"
            img.save(path)
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            prompt, ok = QInputDialog.getText(self, "屏幕分析", "想让我重点分析什么？", text="请描述当前屏幕内容，并给出建议。")
            if not ok: return
            content = [{"type":"text","text":prompt or "请描述当前屏幕内容。"},
                       {"type":"image_url","image_url":{"url":"data:image/png;base64,"+b64}}]
            self.append("你", "[已确认分享当前屏幕截图] " + (prompt or "请描述当前屏幕内容。"))
            self.worker = Worker(self.cfg, [{"role":"system","content":self.cfg["system_prompt"]},{"role":"user","content":content}])
            self.send_btn.setEnabled(False); self.send_btn.setText("分析中…")
            self.worker.done.connect(self.on_reply); self.worker.failed.connect(self.on_error); self.worker.start()
        except Exception as e:
            QMessageBox.critical(self, "截图失败", str(e))

    def toggle_float(self):
        self.floating.setVisible(not self.floating.isVisible())

    def load_todos(self):
        return load_json(TODO_FILE, [])

    def refresh_todos(self):
        self.todo_list.clear()
        for item in self.load_todos(): self.todo_list.addItem(item)

    def add_todo(self):
        value = self.todo_input.text().strip()
        if not value: return
        todos = self.load_todos(); todos.append(value); save_json(TODO_FILE, todos)
        self.todo_input.clear(); self.refresh_todos()

    def remove_todo(self):
        idx = self.todo_list.currentRow()
        if idx < 0: return
        todos = self.load_todos(); todos.pop(idx); save_json(TODO_FILE, todos); self.refresh_todos()

    def closeEvent(self, event):
        event.ignore(); self.hide()
        self.tray.showMessage("智伴 AI", "已缩到系统托盘，仍在后台运行。", QSystemTrayIcon.Information, 1800)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
