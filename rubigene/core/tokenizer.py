"""
English Tokenizer Module

Tokenizes English subtitle text using spaCy for NLP processing.
"""

import re
from dataclasses import dataclass
from typing import List, Set, Optional, Dict, Any
import spacy
from spacy.tokens import Token, Doc


@dataclass
class TokenInfo:
    """Information about a single token."""
    text: str
    lemma: str
    pos: str  # Part of speech tag
    tag: str  # Fine-grained POS tag
    is_stop: bool
    is_punct: bool
    is_alpha: bool
    is_digit: bool
    start_char: int
    end_char: int
    
    def __hash__(self):
        return hash((self.text.lower(), self.lemma.lower()))
    
    def __eq__(self, other):
        if isinstance(other, TokenInfo):
            return self.text.lower() == other.text.lower()
        return False


class EnglishTokenizer:
    """
    Tokenizes English text using spaCy.
    
    Features:
    - Word tokenization
    - Lemmatization
    - POS tagging
    - Punctuation and stopword filtering
    - Proper noun detection
    """
    
    # spaCy model to use (small model for efficiency)
    MODEL_NAME = "en_core_web_sm"
    
    # POS tags mapping to readable names
    POS_NAMES = {
        'NOUN': '名詞',
        'VERB': '動詞',
        'ADJ': '形容詞',
        'ADV': '副詞',
        'PROPN': '固有名詞',
        'PRON': '代名詞',
        'DET': '限定詞',
        'ADP': '前置詞',
        'CONJ': '接続詞',
        'CCONJ': '等位接続詞',
        'SCONJ': '従属接続詞',
        'AUX': '助動詞',
        'INTJ': '間投詞',
        'NUM': '数詞',
        'PART': '不変化詞',
        'PUNCT': '句読点',
        'SYM': '記号',
        'X': 'その他',
    }
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the tokenizer with spaCy model.
        
        Args:
            model_name: Name of spaCy model to load. Defaults to en_core_web_sm.
        """
        self.model_name = model_name or self.MODEL_NAME
        self._nlp: Optional[spacy.Language] = None
        
    @property
    def nlp(self) -> spacy.Language:
        """Lazy-load spaCy model."""
        if self._nlp is None:
            try:
                self._nlp = spacy.load(self.model_name)
            except OSError:
                # Model not installed, try to download it
                import subprocess
                subprocess.run(
                    ["python", "-m", "spacy", "download", self.model_name],
                    check=True
                )
                self._nlp = spacy.load(self.model_name)
        return self._nlp
    
    def tokenize(self, text: str) -> List[TokenInfo]:
        """
        Tokenize text and return token information.
        
        Args:
            text: English text to tokenize.
            
        Returns:
            List of TokenInfo objects for each token.
        """
        doc = self.nlp(text)
        tokens = []
        
        for token in doc:
            token_info = TokenInfo(
                text=token.text,
                lemma=token.lemma_,
                pos=token.pos_,
                tag=token.tag_,
                is_stop=token.is_stop,
                is_punct=token.is_punct,
                is_alpha=token.is_alpha,
                is_digit=token.is_digit,
                start_char=token.idx,
                end_char=token.idx + len(token.text)
            )
            tokens.append(token_info)
        
        return tokens
    
    def tokenize_clean(
        self,
        text: str,
        remove_punct: bool = True,
        remove_stopwords: bool = False,
        remove_numbers: bool = True,
        min_length: int = 2
    ) -> List[TokenInfo]:
        """
        Tokenize text with noise removal.
        
        Args:
            text: English text to tokenize.
            remove_punct: Remove punctuation tokens.
            remove_stopwords: Remove common stopwords.
            remove_numbers: Remove numeric tokens.
            min_length: Minimum token length to keep.
            
        Returns:
            Filtered list of TokenInfo objects.
        """
        tokens = self.tokenize(text)
        filtered = []
        
        for token in tokens:
            # Skip based on filters
            if remove_punct and token.is_punct:
                continue
            if remove_stopwords and token.is_stop:
                continue
            if remove_numbers and token.is_digit:
                continue
            if len(token.text) < min_length:
                continue
            if not token.is_alpha:
                continue
            
            filtered.append(token)
        
        return filtered
    
    def get_words_by_pos(
        self,
        text: str,
        pos_filter: Optional[Set[str]] = None,
        exclude_proper_nouns: bool = False
    ) -> List[TokenInfo]:
        """
        Get words filtered by part of speech.
        
        Args:
            text: English text to tokenize.
            pos_filter: Set of POS tags to include (e.g., {'NOUN', 'VERB'}).
            exclude_proper_nouns: Whether to exclude proper nouns.
            
        Returns:
            Filtered list of TokenInfo objects.
        """
        tokens = self.tokenize_clean(text)
        filtered = []
        
        for token in tokens:
            # Apply POS filter
            if pos_filter and token.pos not in pos_filter:
                continue
            
            # Exclude proper nouns if requested
            if exclude_proper_nouns and token.pos == 'PROPN':
                continue
            
            filtered.append(token)
        
        return filtered
    
    def get_unique_lemmas(
        self,
        text: str,
        pos_filter: Optional[Set[str]] = None
    ) -> Dict[str, TokenInfo]:
        """
        Get unique lemmas from text.
        
        Args:
            text: English text to tokenize.
            pos_filter: Set of POS tags to include.
            
        Returns:
            Dictionary mapping lemma to TokenInfo.
        """
        tokens = self.get_words_by_pos(text, pos_filter)
        unique = {}
        
        for token in tokens:
            lemma_lower = token.lemma.lower()
            if lemma_lower not in unique:
                unique[lemma_lower] = token
        
        return unique
    
    def process_subtitle_lines(
        self,
        lines: List[str],
        pos_filter: Optional[Set[str]] = None,
        exclude_proper_nouns: bool = False
    ) -> Dict[str, List[TokenInfo]]:
        """
        Process multiple subtitle lines and extract tokens.
        
        Args:
            lines: List of subtitle text lines.
            pos_filter: Set of POS tags to include.
            exclude_proper_nouns: Whether to exclude proper nouns.
            
        Returns:
            Dictionary mapping line index to list of tokens.
        """
        results = {}
        
        for i, line in enumerate(lines):
            # Clean HTML tags if present
            clean_line = self._clean_subtitle_text(line)
            tokens = self.get_words_by_pos(
                clean_line,
                pos_filter=pos_filter,
                exclude_proper_nouns=exclude_proper_nouns
            )
            results[i] = tokens
        
        return results
    
    def _clean_subtitle_text(self, text: str) -> str:
        """
        Clean subtitle text by removing formatting tags.
        
        Args:
            text: Raw subtitle text.
            
        Returns:
            Cleaned text.
        """
        # Remove HTML/XML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove ASS formatting codes
        text = re.sub(r'\{[^}]+\}', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @classmethod
    def get_pos_name_ja(cls, pos: str) -> str:
        """Get Japanese name for POS tag."""
        return cls.POS_NAMES.get(pos, pos)
    
    @classmethod
    def ensure_model_installed(cls, model_name: Optional[str] = None) -> bool:
        """
        Ensure spaCy model is installed.
        
        Args:
            model_name: Model name to check/install.
            
        Returns:
            True if model is available.
        """
        model = model_name or cls.MODEL_NAME
        try:
            spacy.load(model)
            return True
        except OSError:
            try:
                import subprocess
                subprocess.run(
                    ["python", "-m", "spacy", "download", model],
                    check=True
                )
                return True
            except subprocess.CalledProcessError:
                return False
