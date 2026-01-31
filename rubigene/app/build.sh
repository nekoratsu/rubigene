#!/bin/bash
# Rubigene Build Script for macOS
# Creates a standalone .app bundle using py2app

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"

echo "=========================================="
echo "Rubigene macOS Build Script"
echo "=========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

# Navigate to project root
cd "$PROJECT_ROOT"

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e ".[build]"

# Download spaCy model if not present
echo ""
echo "Checking spaCy model..."
python3 -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || \
    python3 -m spacy download en_core_web_sm

# Create setup.py for py2app
echo ""
echo "Creating py2app setup..."
cat > "$BUILD_DIR/setup.py" << 'EOF'
"""
py2app build script for Rubigene
"""
from setuptools import setup
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

APP = ['rubigene/gui/app.py']
DATA_FILES = [
    ('rubigene/core', ['rubigene/core/config.yaml']),
    ('rubigene/data', [
        'rubigene/data/ngsl.csv',
        'rubigene/data/cefr.csv',
        'rubigene/data/frequency.json',
        'rubigene/data/translation_cache.json',
    ]),
    ('rubigene/gui', ['rubigene/gui/style.qss']),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'rubigene/app/icon.icns',
    'plist': {
        'CFBundleName': 'Rubigene',
        'CFBundleDisplayName': 'Rubigene',
        'CFBundleIdentifier': 'app.rubigene.Rubigene',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '14.0',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'SRT Subtitle',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': ['public.srt'],
                'CFBundleTypeExtensions': ['srt'],
            }
        ],
    },
    'packages': [
        'rubigene',
        'PySide6',
        'spacy',
        'chardet',
        'yaml',
    ],
    'includes': [
        'rubigene.core',
        'rubigene.gui',
    ],
    'excludes': [
        'matplotlib',
        'numpy.testing',
        'scipy',
        'pandas',
        'PIL',
    ],
}

setup(
    name='Rubigene',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
EOF

# Run py2app
echo ""
echo "Building application bundle..."
cd "$PROJECT_ROOT"
python3 "$BUILD_DIR/setup.py" py2app --dist-dir "$DIST_DIR"

# Verify build
if [ -d "$DIST_DIR/Rubigene.app" ]; then
    echo ""
    echo "=========================================="
    echo "Build successful!"
    echo "Application: $DIST_DIR/Rubigene.app"
    echo "=========================================="
    
    # Get app size
    APP_SIZE=$(du -sh "$DIST_DIR/Rubigene.app" | cut -f1)
    echo "Application size: $APP_SIZE"
    
    # Optional: Create DMG
    if command -v create-dmg &> /dev/null; then
        echo ""
        echo "Creating DMG installer..."
        create-dmg \
            --volname "Rubigene" \
            --window-pos 200 120 \
            --window-size 600 400 \
            --icon-size 100 \
            --icon "Rubigene.app" 150 190 \
            --app-drop-link 450 185 \
            "$DIST_DIR/Rubigene-1.0.0.dmg" \
            "$DIST_DIR/Rubigene.app"
    fi
else
    echo ""
    echo "Build failed!"
    exit 1
fi

# Deactivate virtual environment
deactivate

echo ""
echo "Done!"
