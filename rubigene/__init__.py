# Rubigene
"""
Rubigene - 英語字幕に日本語ルビを自動付与するmacOSアプリケーション

Rubigene automatically adds Japanese ruby annotations to English subtitles.
"""

__version__ = "1.0.0"
__author__ = "Rubigene Team"
__license__ = "MIT"

from .core import (
    SRTLoader,
    SubtitleEntry,
    EnglishTokenizer,
    DifficultyChecker,
    DeepLTranslator,
    RubyTagGenerator,
    RubySubsGenerator,
    RubygenePipeline,
)

__all__ = [
    '__version__',
    'SRTLoader',
    'SubtitleEntry',
    'EnglishTokenizer',
    'DifficultyChecker',
    'DeepLTranslator',
    'RubyTagGenerator',
    'RubySubsGenerator',
    'RubygenePipeline',
]
