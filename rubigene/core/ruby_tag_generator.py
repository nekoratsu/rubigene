"""
Ruby Tag Generator Module

Generates r{word|translation} ruby tags for English text.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from .tokenizer import TokenInfo
from .difficulty_checker import WordDifficulty
from .translator import TranslationResult


@dataclass
class RubyTag:
    """Represents a single ruby annotation."""
    original: str
    ruby: str
    start_pos: int
    end_pos: int
    
    def to_tag(self) -> str:
        """Generate r{original|ruby} tag format."""
        return f"r{{{self.original}|{self.ruby}}}"
    
    def __str__(self) -> str:
        return self.to_tag()


class RubyTagGenerator:
    """
    Generates ruby-annotated text by inserting r{word|translation} tags.
    
    Takes original text, difficult words, and translations to produce
    annotated text suitable for rubysubs processing.
    """
    
    # Ruby tag pattern for parsing
    RUBY_TAG_PATTERN = re.compile(r'r\{([^|]+)\|([^}]+)\}')
    
    def __init__(self):
        """Initialize ruby tag generator."""
        self.generated_tags: List[RubyTag] = []
    
    def generate_ruby_text(
        self,
        original_text: str,
        difficult_words: List[Tuple[TokenInfo, WordDifficulty]],
        translations: Dict[str, TranslationResult]
    ) -> str:
        """
        Generate text with ruby tags inserted.
        
        Args:
            original_text: Original English subtitle text.
            difficult_words: List of (token, difficulty) tuples.
            translations: Dictionary of word -> TranslationResult.
            
        Returns:
            Text with r{word|translation} tags inserted.
        """
        if not difficult_words:
            return original_text
        
        # Build list of ruby tags with positions
        self.generated_tags = []
        
        # Sort by position (end position descending for safe replacement)
        sorted_words = sorted(
            difficult_words,
            key=lambda x: x[0].start_char,
            reverse=True
        )
        
        result = original_text
        processed_positions = set()
        
        for token, difficulty in sorted_words:
            # Skip if already processed (same word at same position)
            pos_key = (token.start_char, token.end_char)
            if pos_key in processed_positions:
                continue
            processed_positions.add(pos_key)
            
            # Get translation
            word_lower = token.text.lower()
            lemma_lower = token.lemma.lower()
            
            trans_result = (
                translations.get(word_lower) or 
                translations.get(lemma_lower)
            )
            
            if not trans_result or not trans_result.is_valid:
                continue
            
            # Create ruby tag
            ruby_tag = RubyTag(
                original=token.text,
                ruby=trans_result.translation,
                start_pos=token.start_char,
                end_pos=token.end_char
            )
            self.generated_tags.append(ruby_tag)
            
            # Replace in text (working backwards to preserve positions)
            result = (
                result[:token.start_char] +
                ruby_tag.to_tag() +
                result[token.end_char:]
            )
        
        return result
    
    def generate_for_line(
        self,
        line: str,
        tokens: List[TokenInfo],
        difficulties: List[WordDifficulty],
        translations: Dict[str, TranslationResult]
    ) -> str:
        """
        Generate ruby text for a single subtitle line.
        
        Args:
            line: Original subtitle line text.
            tokens: List of TokenInfo from tokenization.
            difficulties: List of WordDifficulty assessments.
            translations: Dictionary of translations.
            
        Returns:
            Line with ruby tags inserted.
        """
        # Pair tokens with their difficulties
        difficult_pairs = []
        
        for token, diff in zip(tokens, difficulties):
            if diff.needs_ruby:
                difficult_pairs.append((token, diff))
        
        return self.generate_ruby_text(line, difficult_pairs, translations)
    
    def batch_generate(
        self,
        lines: List[str],
        line_tokens: Dict[int, List[TokenInfo]],
        difficulties: Dict[int, List[WordDifficulty]],
        translations: Dict[str, TranslationResult]
    ) -> List[str]:
        """
        Generate ruby text for multiple subtitle lines.
        
        Args:
            lines: List of original subtitle lines.
            line_tokens: Dictionary mapping line index to tokens.
            difficulties: Dictionary mapping line index to difficulties.
            translations: Dictionary of word -> TranslationResult.
            
        Returns:
            List of lines with ruby tags inserted.
        """
        results = []
        
        for i, line in enumerate(lines):
            tokens = line_tokens.get(i, [])
            diffs = difficulties.get(i, [])
            
            if tokens and diffs:
                result = self.generate_for_line(
                    line, tokens, diffs, translations
                )
            else:
                result = line
            
            results.append(result)
        
        return results
    
    @classmethod
    def parse_ruby_tags(cls, text: str) -> List[RubyTag]:
        """
        Parse ruby tags from annotated text.
        
        Args:
            text: Text containing r{word|ruby} tags.
            
        Returns:
            List of RubyTag objects.
        """
        tags = []
        for match in cls.RUBY_TAG_PATTERN.finditer(text):
            tags.append(RubyTag(
                original=match.group(1),
                ruby=match.group(2),
                start_pos=match.start(),
                end_pos=match.end()
            ))
        return tags
    
    @classmethod
    def strip_ruby_tags(cls, text: str) -> str:
        """
        Remove ruby tags, keeping only the original text.
        
        Args:
            text: Text containing r{word|ruby} tags.
            
        Returns:
            Text with tags replaced by original words.
        """
        return cls.RUBY_TAG_PATTERN.sub(r'\1', text)
    
    @classmethod
    def extract_ruby_only(cls, text: str) -> str:
        """
        Remove ruby tags, keeping only the ruby text.
        
        Args:
            text: Text containing r{word|ruby} tags.
            
        Returns:
            Text with tags replaced by ruby annotations.
        """
        return cls.RUBY_TAG_PATTERN.sub(r'\2', text)
    
    def get_statistics(self) -> Dict:
        """Get statistics about generated ruby tags."""
        return {
            'total_tags': len(self.generated_tags),
            'unique_words': len(set(t.original.lower() for t in self.generated_tags)),
            'tags': [t.to_tag() for t in self.generated_tags]
        }


def create_ruby_text_simple(
    text: str,
    word_translations: Dict[str, str]
) -> str:
    """
    Simple helper to create ruby text from word-translation pairs.
    
    Args:
        text: Original English text.
        word_translations: Dictionary mapping words to Japanese translations.
        
    Returns:
        Text with ruby tags for translated words.
    """
    result = text
    
    # Sort by word length (longest first) to handle compound words
    sorted_words = sorted(
        word_translations.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )
    
    for word, translation in sorted_words:
        if not translation:
            continue
        
        # Replace whole words only (case insensitive)
        pattern = re.compile(
            r'\b' + re.escape(word) + r'\b',
            re.IGNORECASE
        )
        
        def replace_with_ruby(match):
            original = match.group(0)
            return f"r{{{original}|{translation}}}"
        
        result = pattern.sub(replace_with_ruby, result)
    
    return result
