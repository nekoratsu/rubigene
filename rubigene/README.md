# Rubigene

**英語字幕に日本語ルビを自動付与するmacOSアプリケーション**

Rubigene is a macOS desktop application that automatically adds Japanese ruby (furigana) annotations to English subtitles. It uses natural language processing to identify difficult English words and translates them via DeepL API.

## Features

- 🎬 **SRT Subtitle Support**: Load standard SRT subtitle files
- 📚 **Smart Word Detection**: Uses NGSL, CEFR, and frequency data to identify difficult words
- 🌐 **DeepL Translation**: Translates difficult words to Japanese via DeepL API
- 📝 **ASS Output**: Generates ASS subtitle files with ruby annotations
- 💾 **Translation Cache**: Caches translations to reduce API calls
- 🎛️ **Configurable**: Customize difficulty thresholds and POS filters

## Requirements

- macOS 14.0 or later
- Python 3.10+
- DeepL API key (free tier available)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/rubigene.git
cd rubigene

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Download spaCy model
python -m spacy download en_core_web_sm

# Run the application
python -m rubigene.gui.app
```

### Build macOS App

```bash
# Make build script executable
chmod +x app/build.sh

# Run build script
./app/build.sh

# The app will be in dist/Rubigene.app
```

## Usage

1. **Select SRT File**: Click "SRT を選択" and choose your subtitle file
2. **Configure Settings**: Adjust difficulty thresholds and POS filters as needed
3. **Enter API Key**: Enter your DeepL API key (optionally save it)
4. **Select Output Folder**: Choose where to save the generated ASS file
5. **Generate**: Click "ルビ付き字幕を生成する" to start processing

## Configuration

### Difficulty Thresholds

- **NGSL Level**: Words at or above this level get ruby annotations (1-3)
- **CEFR Level**: Words at or above this level get ruby annotations (A1-C2)
- **Frequency Threshold**: Words ranked higher than this get ruby annotations

### POS Filters

Select which parts of speech should receive ruby annotations:
- 名詞 (Nouns)
- 動詞 (Verbs)
- 形容詞 (Adjectives)
- 副詞 (Adverbs)
- 固有名詞を除外 (Exclude proper nouns)

## Project Structure

```
rubigene/
├── core/                 # Core processing modules
│   ├── srt_loader.py     # SRT file parsing
│   ├── tokenizer.py      # English text tokenization (spaCy)
│   ├── difficulty_checker.py  # Word difficulty evaluation
│   ├── translator.py     # DeepL API translation
│   ├── ruby_tag_generator.py  # Ruby tag generation
│   ├── rubysubs_wrapper.py    # ASS file generation
│   ├── pipeline.py       # Processing pipeline orchestration
│   └── utils.py          # Utility functions
├── gui/                  # PySide6 GUI components
│   ├── main_window.py    # Main application window
│   ├── components.py     # Reusable UI components
│   ├── style.qss         # Qt stylesheet
│   └── app.py            # Application entry point
├── data/                 # Data files
│   ├── ngsl.csv          # NGSL vocabulary list
│   ├── cefr.csv          # CEFR vocabulary list
│   ├── frequency.json    # Word frequency data
│   └── translation_cache.json  # Translation cache
├── app/                  # Build configuration
│   ├── pyproject.toml    # Project metadata
│   ├── build.sh          # macOS build script
│   └── icon.icns         # Application icon
└── tests/                # Test suite
    ├── test_tokenizer.py
    ├── test_difficulty_checker.py
    ├── test_translator.py
    ├── test_ruby_tag_generator.py
    └── test_pipeline.py
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=rubigene
```

### Code Style

```bash
# Format code
black rubigene tests

# Lint code
ruff check rubigene tests

# Type checking
mypy rubigene
```

## License

MIT License

## Acknowledgments

- [spaCy](https://spacy.io/) for NLP processing
- [DeepL](https://www.deepl.com/) for translation API
- [PySide6](https://doc.qt.io/qtforpython/) for the GUI framework
- [NGSL](http://www.newgeneralservicelist.org/) for vocabulary data
