"""
Rubigene GUI Components

Reusable UI components for the main window.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QCheckBox, QSpinBox, QTextEdit, QFileDialog,
    QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class FileSelector(QWidget):
    """
    ① 入力ファイル（SRT）選択コンポーネント
    """
    file_selected = Signal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._initial_dir = str(Path.home())
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Button row
        button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("SRT を選択")
        self.select_button.setMinimumWidth(120)
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
            QPushButton:pressed {
                background-color: #2a6bb8;
            }
        """)
        self.select_button.clicked.connect(self._on_select_clicked)
        button_layout.addWidget(self.select_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Path display
        path_layout = QHBoxLayout()
        path_label = QLabel("選択中のファイル:")
        path_label.setStyleSheet("color: #666;")
        path_layout.addWidget(path_label)
        
        self.path_display = QLabel("（未選択）")
        self.path_display.setStyleSheet("color: #333; font-weight: bold;")
        self.path_display.setWordWrap(True)
        path_layout.addWidget(self.path_display, 1)
        
        layout.addLayout(path_layout)
    
    def _on_select_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "SRTファイルを選択",
            self._initial_dir,
            "SRT Files (*.srt);;All Files (*)"
        )
        
        if file_path:
            self.path_display.setText(file_path)
            self._initial_dir = str(Path(file_path).parent)
            self.file_selected.emit(file_path)
    
    def get_file_path(self) -> str:
        path = self.path_display.text()
        return "" if path == "（未選択）" else path
    
    def set_initial_dir(self, dir_path: str):
        self._initial_dir = dir_path


class DifficultySettings(QWidget):
    """
    ② ルビ付与の条件設定コンポーネント
    """
    
    NGSL_LEVELS = ["レベル1 以上", "レベル2 以上", "レベル3 以上"]
    CEFR_LEVELS = ["A1 以上", "A2 以上", "B1 以上", "B2 以上", "C1 以上", "C2 以上"]
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 難易度基準グループ
        criteria_group = QGroupBox("難易度基準")
        criteria_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        criteria_layout = QGridLayout(criteria_group)
        criteria_layout.setSpacing(10)
        
        # NGSL レベル
        criteria_layout.addWidget(QLabel("NGSL レベル"), 0, 0)
        self.ngsl_combo = QComboBox()
        self.ngsl_combo.addItems(self.NGSL_LEVELS)
        self.ngsl_combo.setCurrentIndex(2)  # レベル3 以上
        criteria_layout.addWidget(self.ngsl_combo, 0, 1)
        
        # CEFR レベル
        criteria_layout.addWidget(QLabel("CEFR レベル"), 1, 0)
        self.cefr_combo = QComboBox()
        self.cefr_combo.addItems(self.CEFR_LEVELS)
        self.cefr_combo.setCurrentIndex(2)  # B1 以上
        criteria_layout.addWidget(self.cefr_combo, 1, 1)
        
        # 頻度閾値
        criteria_layout.addWidget(QLabel("頻度閾値"), 2, 0)
        freq_layout = QHBoxLayout()
        self.frequency_spin = QSpinBox()
        self.frequency_spin.setRange(100, 50000)
        self.frequency_spin.setValue(3000)
        self.frequency_spin.setSingleStep(100)
        freq_layout.addWidget(self.frequency_spin)
        freq_layout.addWidget(QLabel("位より難しい単語にルビを付与"))
        freq_layout.addStretch()
        criteria_layout.addLayout(freq_layout, 2, 1)
        
        layout.addWidget(criteria_group)
        
        # 品詞フィルタグループ
        pos_group = QGroupBox("品詞フィルタ")
        pos_group.setStyleSheet(criteria_group.styleSheet())
        pos_layout = QVBoxLayout(pos_group)
        
        # Checkboxes row 1
        row1 = QHBoxLayout()
        self.noun_check = QCheckBox("名詞")
        self.noun_check.setChecked(True)
        row1.addWidget(self.noun_check)
        
        self.verb_check = QCheckBox("動詞")
        self.verb_check.setChecked(True)
        row1.addWidget(self.verb_check)
        
        self.adj_check = QCheckBox("形容詞")
        row1.addWidget(self.adj_check)
        
        self.adv_check = QCheckBox("副詞")
        row1.addWidget(self.adv_check)
        row1.addStretch()
        pos_layout.addLayout(row1)
        
        # Proper noun exclusion
        self.proper_noun_check = QCheckBox("固有名詞を除外する")
        pos_layout.addWidget(self.proper_noun_check)
        
        layout.addWidget(pos_group)
    
    def get_values(self) -> Dict[str, Any]:
        """Get all difficulty setting values."""
        ngsl_index = self.ngsl_combo.currentIndex()
        cefr_text = self.cefr_combo.currentText()
        
        # Extract CEFR level from text (e.g., "B1 以上" -> "B1")
        cefr_level = cefr_text.split()[0]
        
        return {
            'ngsl_level': ngsl_index + 1,  # 1-indexed
            'cefr_level': cefr_level,
            'frequency': self.frequency_spin.value(),
            'include_nouns': self.noun_check.isChecked(),
            'include_verbs': self.verb_check.isChecked(),
            'include_adjectives': self.adj_check.isChecked(),
            'include_adverbs': self.adv_check.isChecked(),
            'exclude_proper_nouns': self.proper_noun_check.isChecked()
        }
    
    def set_values(
        self,
        ngsl_level: int = 3,
        cefr_level: str = "B1",
        frequency: int = 3000,
        include_nouns: bool = True,
        include_verbs: bool = True,
        include_adjectives: bool = False,
        include_adverbs: bool = False,
        exclude_proper_nouns: bool = False
    ):
        """Set difficulty setting values."""
        self.ngsl_combo.setCurrentIndex(max(0, ngsl_level - 1))
        
        cefr_map = {'A1': 0, 'A2': 1, 'B1': 2, 'B2': 3, 'C1': 4, 'C2': 5}
        self.cefr_combo.setCurrentIndex(cefr_map.get(cefr_level, 2))
        
        self.frequency_spin.setValue(frequency)
        self.noun_check.setChecked(include_nouns)
        self.verb_check.setChecked(include_verbs)
        self.adj_check.setChecked(include_adjectives)
        self.adv_check.setChecked(include_adverbs)
        self.proper_noun_check.setChecked(exclude_proper_nouns)


class APISettings(QWidget):
    """
    ③ DeepL API 設定コンポーネント
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # API Key input
        key_layout = QHBoxLayout()
        key_label = QLabel("APIキー:")
        key_label.setMinimumWidth(80)
        key_layout.addWidget(key_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("DeepL APIキーを入力")
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #4a90d9;
            }
        """)
        key_layout.addWidget(self.api_key_input)
        
        layout.addLayout(key_layout)
        
        # Save checkbox
        self.save_key_check = QCheckBox("APIキーを保存する")
        self.save_key_check.setStyleSheet("color: #666;")
        layout.addWidget(self.save_key_check)
    
    def get_api_key(self) -> str:
        return self.api_key_input.text().strip()
    
    def set_api_key(self, key: str):
        self.api_key_input.setText(key)
    
    def should_save_key(self) -> bool:
        return self.save_key_check.isChecked()
    
    def set_save_key(self, save: bool):
        self.save_key_check.setChecked(save)


class OutputSettings(QWidget):
    """
    ④ 出力先フォルダ設定コンポーネント
    """
    folder_selected = Signal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._initial_dir = str(Path.home())
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Button row
        button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("出力フォルダを選択")
        self.select_button.setMinimumWidth(160)
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
            QPushButton:pressed {
                background-color: #3c9e3c;
            }
        """)
        self.select_button.clicked.connect(self._on_select_clicked)
        button_layout.addWidget(self.select_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Path display
        path_layout = QHBoxLayout()
        path_label = QLabel("出力先:")
        path_label.setStyleSheet("color: #666;")
        path_layout.addWidget(path_label)
        
        self.path_display = QLabel("（未選択）")
        self.path_display.setStyleSheet("color: #333; font-weight: bold;")
        self.path_display.setWordWrap(True)
        path_layout.addWidget(self.path_display, 1)
        
        layout.addLayout(path_layout)
    
    def _on_select_clicked(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "出力フォルダを選択",
            self._initial_dir
        )
        
        if folder_path:
            self.path_display.setText(folder_path)
            self._initial_dir = folder_path
            self.folder_selected.emit(folder_path)
    
    def get_output_folder(self) -> str:
        path = self.path_display.text()
        return "" if path == "（未選択）" else path
    
    def set_initial_dir(self, dir_path: str):
        self._initial_dir = dir_path


class LogDisplay(QWidget):
    """
    ⑥ ログ（進行状況）表示コンポーネント
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setMinimumHeight(150)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Menlo', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.text_area)
    
    def log(self, message: str):
        """Append a log message."""
        self.text_area.append(message)
        # Auto-scroll to bottom
        scrollbar = self.text_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear(self):
        """Clear all log messages."""
        self.text_area.clear()
    
    def get_text(self) -> str:
        """Get all log text."""
        return self.text_area.toPlainText()


class GenerateButton(QPushButton):
    """
    ⑤ 実行ボタンコンポーネント
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("ルビ付き字幕を生成する", parent)
        self._setup_style()
    
    def _setup_style(self):
        self.setMinimumHeight(50)
        self.setFont(QFont("Hiragino Sans", 14, QFont.Weight.Bold))
        self.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
