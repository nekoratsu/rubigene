"""
RubySubs ASS Generation Module

Generates ASS subtitle files with ruby (furigana) annotations.
Produces a two-line structure with main text and ruby annotations.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from datetime import timedelta

from .srt_loader import SubtitleEntry
from .ruby_tag_generator import RubyTagGenerator


@dataclass
class ASSStyle:
    """ASS subtitle style definition."""
    name: str = "Default"
    fontname: str = "Arial"
    fontsize: int = 48
    primary_color: str = "&H00FFFFFF"  # White
    secondary_color: str = "&H000000FF"  # Red
    outline_color: str = "&H00000000"  # Black
    back_color: str = "&H80000000"  # Semi-transparent black
    bold: int = 0
    italic: int = 0
    underline: int = 0
    strikeout: int = 0
    scale_x: int = 100
    scale_y: int = 100
    spacing: int = 0
    angle: float = 0
    border_style: int = 1
    outline: int = 2
    shadow: int = 1
    alignment: int = 2  # Bottom center
    margin_l: int = 10
    margin_r: int = 10
    margin_v: int = 10
    encoding: int = 1
    
    def to_ass_line(self) -> str:
        """Generate ASS style definition line."""
        return (
            f"Style: {self.name},{self.fontname},{self.fontsize},"
            f"{self.primary_color},{self.secondary_color},"
            f"{self.outline_color},{self.back_color},"
            f"{self.bold},{self.italic},{self.underline},{self.strikeout},"
            f"{self.scale_x},{self.scale_y},{self.spacing},{self.angle},"
            f"{self.border_style},{self.outline},{self.shadow},"
            f"{self.alignment},{self.margin_l},{self.margin_r},{self.margin_v},"
            f"{self.encoding}"
        )


@dataclass
class ASSEvent:
    """ASS subtitle event (dialogue line)."""
    layer: int = 0
    start: str = "0:00:00.00"
    end: str = "0:00:00.00"
    style: str = "Default"
    name: str = ""
    margin_l: int = 0
    margin_r: int = 0
    margin_v: int = 0
    effect: str = ""
    text: str = ""
    
    def to_ass_line(self) -> str:
        """Generate ASS dialogue line."""
        return (
            f"Dialogue: {self.layer},{self.start},{self.end},"
            f"{self.style},{self.name},"
            f"{self.margin_l:04d},{self.margin_r:04d},{self.margin_v:04d},"
            f"{self.effect},{self.text}"
        )


class RubySubsGenerator:
    """
    Generates ASS subtitle files with ruby annotations.
    
    Creates a two-line structure:
    - Main line: English text
    - Ruby line: Japanese translations positioned above words
    """
    
    # Ruby tag pattern
    RUBY_PATTERN = re.compile(r'r\{([^|]+)\|([^}]+)\}')
    
    # Default styles
    DEFAULT_MAIN_STYLE = ASSStyle(
        name="Main",
        fontname="Arial",
        fontsize=48,
        primary_color="&H00FFFFFF",
        alignment=2  # Bottom center
    )
    
    DEFAULT_RUBY_STYLE = ASSStyle(
        name="Ruby",
        fontname="Hiragino Kaku Gothic Pro",
        fontsize=24,
        primary_color="&H0000FFFF",  # Yellow
        alignment=8  # Top center
    )
    
    def __init__(
        self,
        main_style: Optional[ASSStyle] = None,
        ruby_style: Optional[ASSStyle] = None,
        video_width: int = 1920,
        video_height: int = 1080
    ):
        """
        Initialize ASS generator.
        
        Args:
            main_style: Style for main subtitle text.
            ruby_style: Style for ruby annotations.
            video_width: Video width for positioning.
            video_height: Video height for positioning.
        """
        self.main_style = main_style or self.DEFAULT_MAIN_STYLE
        self.ruby_style = ruby_style or self.DEFAULT_RUBY_STYLE
        self.video_width = video_width
        self.video_height = video_height
        
        # Customize ruby style for positioning
        self.ruby_style.name = "Ruby"
        self.ruby_style.alignment = 8  # Top center for ruby line
    
    def seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.cc)."""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        centiseconds = int((seconds % 1) * 100)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
    
    def srt_time_to_ass(self, srt_time: str) -> str:
        """Convert SRT time format to ASS time format."""
        # SRT: HH:MM:SS,mmm -> ASS: H:MM:SS.cc
        srt_time = srt_time.replace(',', '.')
        match = re.match(r'(\d{1,2}):(\d{2}):(\d{2})\.(\d{3})', srt_time)
        if not match:
            return "0:00:00.00"
        
        h, m, s, ms = match.groups()
        centiseconds = int(int(ms) / 10)
        return f"{int(h)}:{m}:{s}.{centiseconds:02d}"
    
    def generate_ass_header(self) -> str:
        """Generate ASS file header section."""
        header = f"""[Script Info]
Title: Rubigene Generated Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: {self.video_width}
PlayResY: {self.video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{self.main_style.to_ass_line()}
{self.ruby_style.to_ass_line()}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header
    
    def process_ruby_text(self, text: str) -> Tuple[str, str]:
        """
        Process text with ruby tags into main and ruby lines.
        
        Args:
            text: Text containing r{word|ruby} tags.
            
        Returns:
            Tuple of (main_text, ruby_text).
        """
        # Extract main text (original words)
        main_text = RubyTagGenerator.strip_ruby_tags(text)
        
        # Build ruby line with positioning
        ruby_parts = []
        tags = RubyTagGenerator.parse_ruby_tags(text)
        
        for tag in tags:
            ruby_parts.append(tag.ruby)
        
        # Simple ruby line (words separated by spaces)
        ruby_text = " ".join(ruby_parts) if ruby_parts else ""
        
        return main_text, ruby_text
    
    def create_dialogue_pair(
        self,
        entry: SubtitleEntry,
        ruby_text: str
    ) -> List[ASSEvent]:
        """
        Create ASS dialogue events for a subtitle entry.
        
        Args:
            entry: Subtitle entry with timing and text.
            ruby_text: Text with r{word|ruby} tags.
            
        Returns:
            List of ASSEvent objects (main and ruby lines).
        """
        events = []
        
        start_time = self.srt_time_to_ass(entry.start_time)
        end_time = self.srt_time_to_ass(entry.end_time)
        
        # Process ruby tags
        main_text, ruby_only = self.process_ruby_text(ruby_text)
        
        # Create main dialogue line
        main_event = ASSEvent(
            layer=0,
            start=start_time,
            end=end_time,
            style="Main",
            text=main_text
        )
        events.append(main_event)
        
        # Create ruby line if there are annotations
        if ruby_only:
            ruby_event = ASSEvent(
                layer=1,
                start=start_time,
                end=end_time,
                style="Ruby",
                text=ruby_only
            )
            events.append(ruby_event)
        
        return events
    
    def generate_ass(
        self,
        entries: List[SubtitleEntry],
        ruby_texts: List[str]
    ) -> str:
        """
        Generate complete ASS subtitle file content.
        
        Args:
            entries: List of subtitle entries with timing.
            ruby_texts: List of texts with ruby tags.
            
        Returns:
            Complete ASS file content as string.
        """
        # Generate header
        content = self.generate_ass_header()
        
        # Generate dialogue events
        for entry, ruby_text in zip(entries, ruby_texts):
            events = self.create_dialogue_pair(entry, ruby_text)
            for event in events:
                content += event.to_ass_line() + "\n"
        
        return content
    
    def save_ass(
        self,
        output_path: str,
        entries: List[SubtitleEntry],
        ruby_texts: List[str]
    ) -> None:
        """
        Generate and save ASS subtitle file.
        
        Args:
            output_path: Path for output ASS file.
            entries: List of subtitle entries with timing.
            ruby_texts: List of texts with ruby tags.
        """
        content = self.generate_ass(entries, ruby_texts)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8-sig') as f:
            f.write(content)
    
    def generate_from_srt_loader(
        self,
        srt_loader,
        ruby_texts: List[str],
        output_path: str
    ) -> None:
        """
        Generate ASS from SRTLoader and ruby texts.
        
        Args:
            srt_loader: SRTLoader instance with loaded subtitles.
            ruby_texts: List of texts with ruby tags.
            output_path: Path for output ASS file.
        """
        self.save_ass(output_path, srt_loader.entries, ruby_texts)


def generate_simple_ruby_ass(
    srt_path: str,
    word_translations: Dict[str, str],
    output_path: str
) -> None:
    """
    Simple helper to generate ruby ASS from SRT and translations.
    
    Args:
        srt_path: Path to input SRT file.
        word_translations: Dictionary mapping words to translations.
        output_path: Path for output ASS file.
    """
    from .srt_loader import SRTLoader
    from .ruby_tag_generator import create_ruby_text_simple
    
    # Load SRT
    loader = SRTLoader(srt_path)
    
    # Generate ruby texts
    ruby_texts = []
    for entry in loader.entries:
        ruby_text = create_ruby_text_simple(entry.text, word_translations)
        ruby_texts.append(ruby_text)
    
    # Generate ASS
    generator = RubySubsGenerator()
    generator.save_ass(output_path, loader.entries, ruby_texts)
