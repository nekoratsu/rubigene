"""
SRT Subtitle Loader Module

Reads and parses SRT subtitle files, extracting timestamps and text.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Iterator
import chardet


@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry with timing and text."""
    index: int
    start_time: str
    end_time: str
    text: str
    
    @property
    def start_seconds(self) -> float:
        """Convert start time to seconds."""
        return self._time_to_seconds(self.start_time)
    
    @property
    def end_seconds(self) -> float:
        """Convert end time to seconds."""
        return self._time_to_seconds(self.end_time)
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return self.end_seconds - self.start_seconds
    
    @staticmethod
    def _time_to_seconds(time_str: str) -> float:
        """Convert SRT time format (HH:MM:SS,mmm) to seconds."""
        # Handle both comma and period as decimal separator
        time_str = time_str.replace(',', '.')
        match = re.match(r'(\d{1,2}):(\d{2}):(\d{2})\.(\d{3})', time_str)
        if not match:
            raise ValueError(f"Invalid time format: {time_str}")
        hours, minutes, seconds, milliseconds = match.groups()
        return (
            int(hours) * 3600 +
            int(minutes) * 60 +
            int(seconds) +
            int(milliseconds) / 1000
        )
    
    @staticmethod
    def seconds_to_time(seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class SRTLoader:
    """
    Loads and parses SRT subtitle files.
    
    Supports:
    - Various text encodings (auto-detection)
    - Multi-line subtitle text
    - Standard SRT format with timing
    """
    
    # Pattern for matching SRT timing lines
    TIMING_PATTERN = re.compile(
        r'(\d{1,2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,\.]\d{3})'
    )
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the SRT loader.
        
        Args:
            file_path: Optional path to SRT file to load immediately.
        """
        self.file_path: Optional[Path] = None
        self.entries: List[SubtitleEntry] = []
        self.encoding: str = 'utf-8'
        
        if file_path:
            self.load(file_path)
    
    def load(self, file_path: str) -> List[SubtitleEntry]:
        """
        Load and parse an SRT file.
        
        Args:
            file_path: Path to the SRT file.
            
        Returns:
            List of SubtitleEntry objects.
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file format is invalid.
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"SRT file not found: {file_path}")
        
        # Detect encoding
        self.encoding = self._detect_encoding(self.file_path)
        
        # Read and parse file
        with open(self.file_path, 'r', encoding=self.encoding, errors='replace') as f:
            content = f.read()
        
        self.entries = self._parse_srt(content)
        return self.entries
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding using chardet."""
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')
        
        # Fallback to utf-8 if detection fails
        if not encoding:
            encoding = 'utf-8'
        
        return encoding
    
    def _parse_srt(self, content: str) -> List[SubtitleEntry]:
        """
        Parse SRT content into subtitle entries.
        
        Args:
            content: Raw SRT file content.
            
        Returns:
            List of SubtitleEntry objects.
        """
        entries = []
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into blocks (separated by blank lines)
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            if not block.strip():
                continue
            
            entry = self._parse_block(block)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_block(self, block: str) -> Optional[SubtitleEntry]:
        """
        Parse a single subtitle block.
        
        Args:
            block: A single subtitle entry block.
            
        Returns:
            SubtitleEntry or None if parsing fails.
        """
        lines = block.strip().split('\n')
        
        if len(lines) < 2:
            return None
        
        # Find index and timing
        index = None
        timing_line_idx = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Try to match timing line
            timing_match = self.TIMING_PATTERN.match(line)
            if timing_match:
                timing_line_idx = i
                break
            
            # Try to parse as index (must be before timing)
            if index is None and line.isdigit():
                index = int(line)
        
        if timing_line_idx is None:
            return None
        
        timing_match = self.TIMING_PATTERN.match(lines[timing_line_idx].strip())
        start_time = timing_match.group(1).replace('.', ',')
        end_time = timing_match.group(2).replace('.', ',')
        
        # Use line number as index if not found
        if index is None:
            index = len(self.entries) + 1
        
        # Collect text lines (everything after timing)
        text_lines = lines[timing_line_idx + 1:]
        text = '\n'.join(line.strip() for line in text_lines if line.strip())
        
        if not text:
            return None
        
        return SubtitleEntry(
            index=index,
            start_time=start_time,
            end_time=end_time,
            text=text
        )
    
    def __iter__(self) -> Iterator[SubtitleEntry]:
        """Iterate over subtitle entries."""
        return iter(self.entries)
    
    def __len__(self) -> int:
        """Return number of subtitle entries."""
        return len(self.entries)
    
    def __getitem__(self, index: int) -> SubtitleEntry:
        """Get subtitle entry by index."""
        return self.entries[index]
    
    def get_total_duration(self) -> float:
        """Get total duration of subtitles in seconds."""
        if not self.entries:
            return 0.0
        return self.entries[-1].end_seconds
    
    def get_text_only(self) -> List[str]:
        """Get list of subtitle texts without timing information."""
        return [entry.text for entry in self.entries]
    
    def save(self, output_path: str, encoding: str = 'utf-8') -> None:
        """
        Save subtitle entries to an SRT file.
        
        Args:
            output_path: Path for output SRT file.
            encoding: Output file encoding.
        """
        with open(output_path, 'w', encoding=encoding) as f:
            for i, entry in enumerate(self.entries, 1):
                f.write(f"{i}\n")
                f.write(f"{entry.start_time} --> {entry.end_time}\n")
                f.write(f"{entry.text}\n")
                f.write("\n")
