"""
Difficulty Checker Module

Evaluates word difficulty using NGSL, CEFR, and frequency data
to determine which words need ruby annotations.
"""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from enum import IntEnum

from .tokenizer import TokenInfo
from .utils import get_data_path


class NGSLLevel(IntEnum):
    """NGSL vocabulary levels (1 = most common)."""
    LEVEL_1 = 1  # Most common 1000 words
    LEVEL_2 = 2  # Next 1000 words
    LEVEL_3 = 3  # Next 1000 words (NGSL total: ~2800 words)
    NOT_IN_NGSL = 99  # Not in NGSL list


class CEFRLevel(IntEnum):
    """CEFR language proficiency levels."""
    A1 = 1  # Beginner
    A2 = 2  # Elementary
    B1 = 3  # Intermediate
    B2 = 4  # Upper Intermediate
    C1 = 5  # Advanced
    C2 = 6  # Proficiency
    UNKNOWN = 99  # Not categorized


@dataclass
class WordDifficulty:
    """Difficulty assessment for a single word."""
    word: str
    lemma: str
    ngsl_level: NGSLLevel
    cefr_level: CEFRLevel
    frequency_rank: int  # Lower = more common
    needs_ruby: bool
    pos: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'word': self.word,
            'lemma': self.lemma,
            'ngsl_level': self.ngsl_level.value,
            'cefr_level': self.cefr_level.value,
            'frequency_rank': self.frequency_rank,
            'needs_ruby': self.needs_ruby,
            'pos': self.pos
        }


class DifficultyChecker:
    """
    Evaluates word difficulty to determine ruby annotation needs.
    
    Uses three data sources:
    - NGSL (New General Service List): Core vocabulary levels
    - CEFR (Common European Framework): Language proficiency levels
    - Frequency data: Word usage frequency rankings
    """
    
    # Default threshold settings
    DEFAULT_NGSL_THRESHOLD = 3  # Level 3+ needs ruby
    DEFAULT_CEFR_THRESHOLD = CEFRLevel.B1  # B1+ needs ruby
    DEFAULT_FREQUENCY_THRESHOLD = 3000  # Rank 3000+ needs ruby
    
    def __init__(
        self,
        ngsl_path: Optional[str] = None,
        cefr_path: Optional[str] = None,
        frequency_path: Optional[str] = None
    ):
        """
        Initialize difficulty checker with vocabulary data.
        
        Args:
            ngsl_path: Path to NGSL CSV file.
            cefr_path: Path to CEFR CSV file.
            frequency_path: Path to frequency JSON file.
        """
        self.ngsl_data: Dict[str, int] = {}
        self.cefr_data: Dict[str, int] = {}
        self.frequency_data: Dict[str, int] = {}
        
        # Load data files
        self._load_ngsl(ngsl_path or get_data_path('ngsl.csv'))
        self._load_cefr(cefr_path or get_data_path('cefr.csv'))
        self._load_frequency(frequency_path or get_data_path('frequency.json'))
        
        # Default thresholds
        self.ngsl_threshold = self.DEFAULT_NGSL_THRESHOLD
        self.cefr_threshold = self.DEFAULT_CEFR_THRESHOLD
        self.frequency_threshold = self.DEFAULT_FREQUENCY_THRESHOLD
        
        # POS filter settings
        self.pos_filter: Set[str] = {'NOUN', 'VERB'}  # Default: nouns and verbs
        self.exclude_proper_nouns = False
    
    def _load_ngsl(self, path: str) -> None:
        """Load NGSL vocabulary data from CSV."""
        file_path = Path(path)
        if not file_path.exists():
            print(f"Warning: NGSL file not found: {path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row.get('word', '').lower().strip()
                level = int(row.get('level', 99))
                if word:
                    self.ngsl_data[word] = level
    
    def _load_cefr(self, path: str) -> None:
        """Load CEFR vocabulary data from CSV."""
        file_path = Path(path)
        if not file_path.exists():
            print(f"Warning: CEFR file not found: {path}")
            return
        
        cefr_map = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row.get('word', '').lower().strip()
                level_str = row.get('level', 'UNKNOWN').upper().strip()
                level = cefr_map.get(level_str, 99)
                if word:
                    self.cefr_data[word] = level
    
    def _load_frequency(self, path: str) -> None:
        """Load word frequency data from JSON."""
        file_path = Path(path)
        if not file_path.exists():
            print(f"Warning: Frequency file not found: {path}")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            self.frequency_data = json.load(f)
    
    def configure(
        self,
        ngsl_threshold: Optional[int] = None,
        cefr_threshold: Optional[CEFRLevel] = None,
        frequency_threshold: Optional[int] = None,
        pos_filter: Optional[Set[str]] = None,
        exclude_proper_nouns: Optional[bool] = None
    ) -> None:
        """
        Configure difficulty thresholds.
        
        Args:
            ngsl_threshold: NGSL level threshold (words at or above need ruby).
            cefr_threshold: CEFR level threshold.
            frequency_threshold: Frequency rank threshold.
            pos_filter: Set of POS tags to include for ruby.
            exclude_proper_nouns: Whether to exclude proper nouns.
        """
        if ngsl_threshold is not None:
            self.ngsl_threshold = ngsl_threshold
        if cefr_threshold is not None:
            self.cefr_threshold = cefr_threshold
        if frequency_threshold is not None:
            self.frequency_threshold = frequency_threshold
        if pos_filter is not None:
            self.pos_filter = pos_filter
        if exclude_proper_nouns is not None:
            self.exclude_proper_nouns = exclude_proper_nouns
    
    def get_ngsl_level(self, word: str) -> NGSLLevel:
        """Get NGSL level for a word."""
        level = self.ngsl_data.get(word.lower(), 99)
        try:
            return NGSLLevel(level)
        except ValueError:
            return NGSLLevel.NOT_IN_NGSL
    
    def get_cefr_level(self, word: str) -> CEFRLevel:
        """Get CEFR level for a word."""
        level = self.cefr_data.get(word.lower(), 99)
        try:
            return CEFRLevel(level)
        except ValueError:
            return CEFRLevel.UNKNOWN
    
    def get_frequency_rank(self, word: str) -> int:
        """Get frequency rank for a word (lower = more common)."""
        return self.frequency_data.get(word.lower(), 999999)
    
    def check_word(self, token: TokenInfo) -> WordDifficulty:
        """
        Check difficulty of a single word.
        
        Args:
            token: TokenInfo for the word to check.
            
        Returns:
            WordDifficulty assessment.
        """
        word = token.text.lower()
        lemma = token.lemma.lower()
        
        # Check by lemma first, then by word form
        ngsl_level = self.get_ngsl_level(lemma)
        if ngsl_level == NGSLLevel.NOT_IN_NGSL:
            ngsl_level = self.get_ngsl_level(word)
        
        cefr_level = self.get_cefr_level(lemma)
        if cefr_level == CEFRLevel.UNKNOWN:
            cefr_level = self.get_cefr_level(word)
        
        freq_rank = min(
            self.get_frequency_rank(lemma),
            self.get_frequency_rank(word)
        )
        
        # Determine if ruby is needed
        needs_ruby = self._evaluate_needs_ruby(
            token, ngsl_level, cefr_level, freq_rank
        )
        
        return WordDifficulty(
            word=token.text,
            lemma=token.lemma,
            ngsl_level=ngsl_level,
            cefr_level=cefr_level,
            frequency_rank=freq_rank,
            needs_ruby=needs_ruby,
            pos=token.pos
        )
    
    def _evaluate_needs_ruby(
        self,
        token: TokenInfo,
        ngsl_level: NGSLLevel,
        cefr_level: CEFRLevel,
        freq_rank: int
    ) -> bool:
        """
        Determine if a word needs ruby annotation.
        
        Uses OR logic: if any threshold is exceeded, ruby is needed.
        """
        # Check POS filter
        if self.pos_filter and token.pos not in self.pos_filter:
            return False
        
        # Check proper noun exclusion
        if self.exclude_proper_nouns and token.pos == 'PROPN':
            return False
        
        # Check difficulty thresholds (any one exceeding triggers ruby)
        is_ngsl_difficult = ngsl_level.value >= self.ngsl_threshold
        is_cefr_difficult = cefr_level.value >= self.cefr_threshold.value
        is_freq_difficult = freq_rank >= self.frequency_threshold
        
        # Word needs ruby if it's not in NGSL OR if any threshold is exceeded
        if ngsl_level == NGSLLevel.NOT_IN_NGSL:
            # Not in NGSL - likely a difficult word
            return True
        
        return is_ngsl_difficult or is_cefr_difficult or is_freq_difficult
    
    def check_tokens(
        self,
        tokens: List[TokenInfo]
    ) -> List[WordDifficulty]:
        """
        Check difficulty of multiple tokens.
        
        Args:
            tokens: List of TokenInfo objects.
            
        Returns:
            List of WordDifficulty assessments.
        """
        return [self.check_word(token) for token in tokens]
    
    def filter_difficult_words(
        self,
        tokens: List[TokenInfo]
    ) -> List[Tuple[TokenInfo, WordDifficulty]]:
        """
        Filter tokens to only those needing ruby.
        
        Args:
            tokens: List of TokenInfo objects.
            
        Returns:
            List of (token, difficulty) tuples for words needing ruby.
        """
        results = []
        seen_lemmas: Set[str] = set()
        
        for token in tokens:
            difficulty = self.check_word(token)
            lemma_lower = token.lemma.lower()
            
            if difficulty.needs_ruby and lemma_lower not in seen_lemmas:
                results.append((token, difficulty))
                seen_lemmas.add(lemma_lower)
        
        return results
    
    def get_statistics(
        self,
        difficulties: List[WordDifficulty]
    ) -> Dict:
        """
        Get statistics about difficulty distribution.
        
        Args:
            difficulties: List of WordDifficulty assessments.
            
        Returns:
            Statistics dictionary.
        """
        total = len(difficulties)
        needs_ruby = sum(1 for d in difficulties if d.needs_ruby)
        
        ngsl_dist = {}
        for d in difficulties:
            level = d.ngsl_level.name
            ngsl_dist[level] = ngsl_dist.get(level, 0) + 1
        
        cefr_dist = {}
        for d in difficulties:
            level = d.cefr_level.name
            cefr_dist[level] = cefr_dist.get(level, 0) + 1
        
        return {
            'total_words': total,
            'words_needing_ruby': needs_ruby,
            'ruby_percentage': (needs_ruby / total * 100) if total > 0 else 0,
            'ngsl_distribution': ngsl_dist,
            'cefr_distribution': cefr_dist
        }
