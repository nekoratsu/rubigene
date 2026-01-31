"""
Rubigene Main Window

Main application window implementing the Japanese wireframe design.
"""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont

from .components import (
    FileSelector,
    DifficultySettings,
    APISettings,
    OutputSettings,
    LogDisplay,
    GenerateButton
)
from ..core.pipeline import RubygenePipeline, PipelineConfig, PipelineProgress
from ..core.difficulty_checker import CEFRLevel
from ..core.utils import load_user_config, save_user_config


class PipelineWorker(QThread):
    """
    Worker thread for running the pipeline without blocking the UI.
    """
    progress = Signal(object)  # PipelineProgress
    finished = Signal(str)  # Output path
    error = Signal(str)  # Error message
    
    def __init__(self, config: PipelineConfig):
        super().__init__()
        self.config = config
        self._pipeline: Optional[RubygenePipeline] = None
    
    def run(self):
        """Execute the pipeline in background thread."""
        try:
            self._pipeline = RubygenePipeline(self.config)
            self._pipeline.set_progress_callback(self._on_progress)
            output_path = self._pipeline.run()
            self.finished.emit(output_path)
        except Exception as e:
            self.error.emit(str(e))
    
    def _on_progress(self, progress: PipelineProgress):
        """Forward progress to main thread."""
        self.progress.emit(progress)


class MainWindow(QMainWindow):
    """
    Main application window for Rubigene.
    
    Implements the Japanese wireframe design with sections:
    ① 入力ファイル（SRT）
    ② ルビ付与の条件設定
    ③ DeepL API 設定
    ④ 出力先フォルダ
    ⑤ 実行
    ⑥ ログ（進行状況）
    """
    
    def __init__(self):
        super().__init__()
        
        self.worker: Optional[PipelineWorker] = None
        self.user_config = load_user_config()
        
        self._setup_window()
        self._setup_ui()
        self._load_saved_settings()
        self._connect_signals()
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("Rubigene – 英語字幕に日本語ルビを自動付与するアプリ")
        self.setMinimumSize(700, 800)
        self.resize(750, 900)
        
        # Center on screen
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _setup_ui(self):
        """Create and layout UI components."""
        # Central widget with scroll area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # App title/header
        header_label = QLabel("Rubigene – 英語字幕に日本語ルビを自動付与するアプリ")
        header_label.setFont(QFont("Hiragino Sans", 16, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #333; padding: 10px;")
        main_layout.addWidget(header_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ccc;")
        main_layout.addWidget(separator)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # ① 入力ファイル（SRT）
        self.file_selector = FileSelector()
        scroll_layout.addWidget(self._create_section("① 入力ファイル（SRT）", self.file_selector))
        
        # ② ルビ付与の条件設定
        self.difficulty_settings = DifficultySettings()
        scroll_layout.addWidget(self._create_section("② ルビ付与の条件設定", self.difficulty_settings))
        
        # ③ DeepL API 設定
        self.api_settings = APISettings()
        scroll_layout.addWidget(self._create_section("③ DeepL API 設定", self.api_settings))
        
        # ④ 出力先フォルダ
        self.output_settings = OutputSettings()
        scroll_layout.addWidget(self._create_section("④ 出力先フォルダ", self.output_settings))
        
        # ⑤ 実行ボタン
        self.generate_button = GenerateButton()
        scroll_layout.addWidget(self.generate_button)
        
        # ⑥ ログ（進行状況）
        self.log_display = LogDisplay()
        scroll_layout.addWidget(self._create_section("⑥ ログ（進行状況）", self.log_display))
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
    
    def _create_section(self, title: str, widget: QWidget) -> QWidget:
        """Create a titled section container."""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Hiragino Sans", 13, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #444; border: none; background: transparent;")
        layout.addWidget(title_label)
        
        widget.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(widget)
        
        return container
    
    def _connect_signals(self):
        """Connect widget signals to slots."""
        self.generate_button.clicked.connect(self._on_generate_clicked)
    
    def _load_saved_settings(self):
        """Load previously saved settings."""
        # Load API key if saved
        if self.user_config.get('api', {}).get('save_api_key', False):
            api_key = self.user_config.get('api', {}).get('api_key', '')
            if api_key:
                self.api_settings.set_api_key(api_key)
                self.api_settings.set_save_key(True)
        
        # Load last used folders
        last_input = self.user_config.get('ui', {}).get('last_input_folder', '')
        last_output = self.user_config.get('ui', {}).get('last_output_folder', '')
        
        if last_input and os.path.isdir(last_input):
            self.file_selector.set_initial_dir(last_input)
        if last_output and os.path.isdir(last_output):
            self.output_settings.set_initial_dir(last_output)
        
        # Load difficulty settings
        diff_config = self.user_config.get('difficulty', {})
        pos_config = self.user_config.get('pos_filter', {})
        
        if diff_config:
            self.difficulty_settings.set_values(
                ngsl_level=diff_config.get('ngsl_threshold', 3),
                cefr_level=diff_config.get('cefr_threshold', 'B1'),
                frequency=diff_config.get('frequency_threshold', 3000),
                include_nouns=pos_config.get('include_nouns', True),
                include_verbs=pos_config.get('include_verbs', True),
                include_adjectives=pos_config.get('include_adjectives', False),
                include_adverbs=pos_config.get('include_adverbs', False),
                exclude_proper_nouns=pos_config.get('exclude_proper_nouns', False)
            )
    
    def _save_settings(self):
        """Save current settings."""
        # Update config with current values
        self.user_config['api']['save_api_key'] = self.api_settings.should_save_key()
        if self.api_settings.should_save_key():
            self.user_config['api']['api_key'] = self.api_settings.get_api_key()
        else:
            self.user_config['api']['api_key'] = ''
        
        # Save folder paths
        input_path = self.file_selector.get_file_path()
        if input_path:
            self.user_config['ui']['last_input_folder'] = str(Path(input_path).parent)
        
        output_path = self.output_settings.get_output_folder()
        if output_path:
            self.user_config['ui']['last_output_folder'] = output_path
        
        # Save difficulty settings
        diff_values = self.difficulty_settings.get_values()
        self.user_config['difficulty']['ngsl_threshold'] = diff_values['ngsl_level']
        self.user_config['difficulty']['cefr_threshold'] = diff_values['cefr_level']
        self.user_config['difficulty']['frequency_threshold'] = diff_values['frequency']
        self.user_config['pos_filter']['include_nouns'] = diff_values['include_nouns']
        self.user_config['pos_filter']['include_verbs'] = diff_values['include_verbs']
        self.user_config['pos_filter']['include_adjectives'] = diff_values['include_adjectives']
        self.user_config['pos_filter']['include_adverbs'] = diff_values['include_adverbs']
        self.user_config['pos_filter']['exclude_proper_nouns'] = diff_values['exclude_proper_nouns']
        
        save_user_config(self.user_config)
    
    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate all input fields before processing."""
        # Check input file
        input_path = self.file_selector.get_file_path()
        if not input_path:
            return False, "SRTファイルを選択してください。"
        if not os.path.exists(input_path):
            return False, "選択されたSRTファイルが見つかりません。"
        
        # Check API key
        api_key = self.api_settings.get_api_key()
        if not api_key:
            return False, "DeepL APIキーを入力してください。"
        
        # Check output folder
        output_folder = self.output_settings.get_output_folder()
        if not output_folder:
            return False, "出力フォルダを選択してください。"
        
        return True, ""
    
    def _build_pipeline_config(self) -> PipelineConfig:
        """Build pipeline configuration from UI values."""
        diff_values = self.difficulty_settings.get_values()
        
        # Map CEFR string to enum
        cefr_map = {
            'A1': CEFRLevel.A1,
            'A2': CEFRLevel.A2,
            'B1': CEFRLevel.B1,
            'B2': CEFRLevel.B2,
            'C1': CEFRLevel.C1,
            'C2': CEFRLevel.C2
        }
        
        return PipelineConfig(
            input_srt_path=self.file_selector.get_file_path(),
            output_folder=self.output_settings.get_output_folder(),
            ngsl_threshold=diff_values['ngsl_level'],
            cefr_threshold=cefr_map.get(diff_values['cefr_level'], CEFRLevel.B1),
            frequency_threshold=diff_values['frequency'],
            include_nouns=diff_values['include_nouns'],
            include_verbs=diff_values['include_verbs'],
            include_adjectives=diff_values['include_adjectives'],
            include_adverbs=diff_values['include_adverbs'],
            exclude_proper_nouns=diff_values['exclude_proper_nouns'],
            deepl_api_key=self.api_settings.get_api_key()
        )
    
    @Slot()
    def _on_generate_clicked(self):
        """Handle generate button click."""
        # Validate inputs
        is_valid, error_msg = self._validate_inputs()
        if not is_valid:
            QMessageBox.warning(self, "入力エラー", error_msg)
            return
        
        # Save settings
        self._save_settings()
        
        # Clear log and disable button
        self.log_display.clear()
        self.generate_button.setEnabled(False)
        self.generate_button.setText("処理中...")
        
        # Build config and start worker
        config = self._build_pipeline_config()
        
        self.worker = PipelineWorker(config)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()
        
        self.log_display.log("処理を開始しました...")
    
    @Slot(object)
    def _on_progress(self, progress: PipelineProgress):
        """Handle progress updates from worker."""
        self.log_display.log(f"- {progress.message}")
    
    @Slot(str)
    def _on_finished(self, output_path: str):
        """Handle successful completion."""
        self.generate_button.setEnabled(True)
        self.generate_button.setText("ルビ付き字幕を生成する")
        
        self.log_display.log(f"✓ ASSファイルを生成しました: {output_path}")
        self.log_display.log("処理が完了しました！")
        
        QMessageBox.information(
            self,
            "完了",
            f"ルビ付きASS字幕を生成しました。\n\n{output_path}"
        )
    
    @Slot(str)
    def _on_error(self, error_msg: str):
        """Handle pipeline error."""
        self.generate_button.setEnabled(True)
        self.generate_button.setText("ルビ付き字幕を生成する")
        
        self.log_display.log(f"✗ エラー: {error_msg}")
        
        QMessageBox.critical(
            self,
            "エラー",
            f"処理中にエラーが発生しました。\n\n{error_msg}"
        )
    
    def closeEvent(self, event):
        """Handle window close."""
        # Wait for worker to finish if running
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "確認",
                "処理中です。終了しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.worker.terminate()
            self.worker.wait()
        
        event.accept()
