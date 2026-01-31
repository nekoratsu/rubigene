"""
Tests for EnglishTokenizer module.
"""

import pytest
from rubigene.core.tokenizer import EnglishTokenizer, TokenInfo


class TestEnglishTokenizer:
    """Test cases for EnglishTokenizer class."""
    
    @pytest.fixture
    def tokenizer(self):
        """Create tokenizer instance for tests."""
        return EnglishTokenizer()
    
    def test_basic_tokenization(self, tokenizer):
        """Test basic text tokenization."""
        text = "The quick brown fox jumps."
        tokens = tokenizer.tokenize(text)
        
        assert len(tokens) > 0
        assert all(isinstance(t, TokenInfo) for t in tokens)
        
        # Check token attributes
        token = tokens[0]
        assert hasattr(token, 'text')
        assert hasattr(token, 'lemma')
        assert hasattr(token, 'pos')
    
    def test_tokenize_clean_removes_punctuation(self, tokenizer):
        """Test that clean tokenization removes punctuation."""
        text = "Hello, world! How are you?"
        tokens = tokenizer.tokenize_clean(text, remove_punct=True)
        
        # No punctuation tokens
        assert not any(t.is_punct for t in tokens)
    
    def test_tokenize_clean_min_length(self, tokenizer):
        """Test minimum length filtering."""
        text = "I am a very good student."
        tokens = tokenizer.tokenize_clean(text, min_length=3)
        
        # All tokens should have length >= 3
        assert all(len(t.text) >= 3 for t in tokens)
    
    def test_pos_filtering(self, tokenizer):
        """Test part-of-speech filtering."""
        text = "The beautiful cat sleeps peacefully."
        tokens = tokenizer.get_words_by_pos(
            text,
            pos_filter={'NOUN', 'VERB'}
        )
        
        # Only nouns and verbs
        assert all(t.pos in {'NOUN', 'VERB'} for t in tokens)
    
    def test_proper_noun_exclusion(self, tokenizer):
        """Test proper noun exclusion."""
        text = "John went to Paris yesterday."
        tokens = tokenizer.get_words_by_pos(
            text,
            exclude_proper_nouns=True
        )
        
        # No proper nouns
        assert not any(t.pos == 'PROPN' for t in tokens)
    
    def test_unique_lemmas(self, tokenizer):
        """Test unique lemma extraction."""
        text = "The cats are running and the dogs are running too."
        lemmas = tokenizer.get_unique_lemmas(text)
        
        # Should have unique lemmas
        assert isinstance(lemmas, dict)
        assert 'run' in lemmas or 'running' in lemmas
    
    def test_clean_subtitle_text(self, tokenizer):
        """Test subtitle text cleaning."""
        text = "<i>Hello</i> world! {\\an8}Test"
        cleaned = tokenizer._clean_subtitle_text(text)
        
        assert '<i>' not in cleaned
        assert '</i>' not in cleaned
        assert '{' not in cleaned
    
    def test_empty_text(self, tokenizer):
        """Test handling of empty text."""
        tokens = tokenizer.tokenize("")
        assert tokens == []
    
    def test_token_positions(self, tokenizer):
        """Test token character positions."""
        text = "Hello world"
        tokens = tokenizer.tokenize(text)
        
        # Check positions are correct
        for token in tokens:
            extracted = text[token.start_char:token.end_char]
            assert extracted == token.text


class TestTokenInfo:
    """Test cases for TokenInfo dataclass."""
    
    def test_token_info_creation(self):
        """Test TokenInfo creation."""
        token = TokenInfo(
            text="running",
            lemma="run",
            pos="VERB",
            tag="VBG",
            is_stop=False,
            is_punct=False,
            is_alpha=True,
            is_digit=False,
            start_char=0,
            end_char=7
        )
        
        assert token.text == "running"
        assert token.lemma == "run"
        assert token.pos == "VERB"
    
    def test_token_info_hash(self):
        """Test TokenInfo hashing."""
        token1 = TokenInfo(
            text="Run", lemma="run", pos="VERB", tag="VB",
            is_stop=False, is_punct=False, is_alpha=True,
            is_digit=False, start_char=0, end_char=3
        )
        token2 = TokenInfo(
            text="run", lemma="run", pos="VERB", tag="VB",
            is_stop=False, is_punct=False, is_alpha=True,
            is_digit=False, start_char=10, end_char=13
        )
        
        # Same word (case-insensitive) should be equal
        assert token1 == token2
        assert hash(token1) == hash(token2)
