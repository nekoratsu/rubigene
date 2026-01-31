"""
Utility Functions for Rubigene

Common utilities and helper functions used across modules.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def get_app_root() -> Path:
    """
    Get the application root directory.
    
    Handles both development and bundled (PyInstaller/py2app) scenarios.
    
    Returns:
        Path to application root directory.
    """
    # Check if running as bundled application
    if getattr(sys, 'frozen', False):
        # Running in a bundle (PyInstaller or py2app)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller bundle
            return Path(sys._MEIPASS)
        else:
            # py2app or similar
            return Path(os.path.dirname(sys.executable)).parent / 'Resources'
    else:
        # Running in development
        return Path(__file__).parent.parent


def get_data_path(filename: str) -> str:
    """
    Get path to a data file.
    
    Args:
        filename: Name of the data file.
        
    Returns:
        Full path to the data file.
    """
    data_dir = get_app_root() / 'data'
    return str(data_dir / filename)


def get_config_path() -> str:
    """
    Get path to the configuration file.
    
    Returns:
        Full path to config.yaml.
    """
    return str(get_app_root() / 'core' / 'config.yaml')


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml.
    
    Returns:
        Configuration dictionary.
    """
    config_path = get_config_path()
    
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    return get_default_config()


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to config.yaml.
    
    Args:
        config: Configuration dictionary to save.
    """
    config_path = get_config_path()
    
    # Ensure directory exists
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration values.
    
    Returns:
        Default configuration dictionary.
    """
    return {
        'difficulty': {
            'ngsl_threshold': 3,
            'cefr_threshold': 'B1',
            'frequency_threshold': 3000
        },
        'pos_filter': {
            'include_nouns': True,
            'include_verbs': True,
            'include_adjectives': False,
            'include_adverbs': False,
            'exclude_proper_nouns': False
        },
        'output': {
            'video_width': 1920,
            'video_height': 1080
        },
        'api': {
            'save_api_key': False,
            'api_key': ''
        },
        'ui': {
            'last_input_folder': '',
            'last_output_folder': ''
        }
    }


def get_user_config_dir() -> Path:
    """
    Get user configuration directory.
    
    Returns:
        Path to user config directory (~/.rubigene or platform-specific).
    """
    if sys.platform == 'darwin':
        # macOS: ~/Library/Application Support/Rubigene
        config_dir = Path.home() / 'Library' / 'Application Support' / 'Rubigene'
    elif sys.platform == 'win32':
        # Windows: %APPDATA%/Rubigene
        appdata = os.environ.get('APPDATA', Path.home())
        config_dir = Path(appdata) / 'Rubigene'
    else:
        # Linux/Other: ~/.config/rubigene
        config_dir = Path.home() / '.config' / 'rubigene'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_user_config_path() -> str:
    """
    Get path to user configuration file.
    
    Returns:
        Full path to user config.yaml.
    """
    return str(get_user_config_dir() / 'config.yaml')


def load_user_config() -> Dict[str, Any]:
    """
    Load user configuration.
    
    Returns:
        User configuration dictionary (merged with defaults).
    """
    config = get_default_config()
    user_config_path = get_user_config_path()
    
    if Path(user_config_path).exists():
        try:
            with open(user_config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f) or {}
                config = deep_merge(config, user_config)
        except Exception:
            pass
    
    return config


def save_user_config(config: Dict[str, Any]) -> None:
    """
    Save user configuration.
    
    Args:
        config: Configuration dictionary to save.
    """
    user_config_path = get_user_config_path()
    
    with open(user_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary.
        override: Dictionary with values to override.
        
    Returns:
        Merged dictionary.
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename.
        
    Returns:
        Sanitized filename.
    """
    # Characters not allowed in filenames
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    
    return filename or 'untitled'


def format_time_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted duration string (e.g., "1:23:45" or "45.2s").
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}時間{minutes}分{secs}秒"


def count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Text to count words in.
        
    Returns:
        Word count.
    """
    return len(text.split())


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate.
        max_length: Maximum length.
        
    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
