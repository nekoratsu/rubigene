"""
Tests for DifficultyChecker module.
"""

import pytest
from unittest.mock import MagicMock, patch
from rubigene.core.difficulty_checker import (
    DifficultyChecker,
    WordDifficulty,
    NGSLLevel,
    CEFRLevel
)
from rubigene.core.tokenizer import TokenInfo


class TestDifficultyChecker:
    """Test cases for DifficultyChecker class."""
    
    @pytest.fixture
    def checker(self):
        """Create difficulty checker with mock data."""
        checker = DifficultyChecker()
        # Add some test data
        checker.ngsl_data = {
            'the': 1, 'a': 1, 'is': 1,
            'book': 2, 'read': 2,
            'eloquent': 99, 'ubiquitous': 99
        }
        checker.cefr_data = {
            'the': 1, 'a': 1, 'is': 1,
            'book': 2, 'read': 2,
            'eloquent': 5, 'ubiquitous': 6
        }
        checker.frequency_data = {
            'the': 1, 'a': 2, 'is': 3,
            'book': 500, 'read': 300,
            'eloquent': 15000, 'ubiquitous': 20000
        }
        return checker
    
    @pytest.fixture
    def token_factory(self):
        """Factory for creating test tokens."""
        def create_token(text, lemma=None, pos='NOUN'):
            return TokenInfo(
                text=text,
                lemma=lemma or text.lower(),
                pos=pos,
                tag='NN',
                is_stop=False,
                is_punct=False,
                is_alpha=True,
                is_digit=False,
                start_char=0,
                end_char=len(text)
            )
        return create_token
    
    def test_ngsl_level_lookup(self, checker):
        """Test NGSL level lookup."""
        assert checker.get_ngsl_level('the') == NGSLLevel.LEVEL_1
        assert checker.get_ngsl_level('book') == NGSLLevel.LEVEL_2
        assert checker.get_ngsl_level('unknown') == NGSLLevel.NOT_IN_NGSL
    
    def test_cefr_level_lookup(self, checker):
        """Test CEFR level lookup."""
        assert checker.get_cefr_level('the') == CEFRLevel.A1
        assert checker.get_cefr_level('eloquent') == CEFRLevel.C1
        assert checker.get_cefr_level('unknown') == CEFRLevel.UNKNOWN
    
    def test_frequency_rank_lookup(self, checker):
        """Test frequency rank lookup."""
        assert checker.get_frequency_rank('the') == 1
        assert checker.get_frequency_rank('book') == 500
        assert checker.get_frequency_rank('unknown') == 999999
    
    def test_check_common_word(self, checker, token_factory):
        """Test difficulty check for common word."""
        token = token_factory('book')
        difficulty = checker.check_word(token)
        
        assert isinstance(difficulty, WordDifficulty)
        assert difficulty.word == 'book'
        assert difficulty.ngsl_level == NGSLLevel.LEVEL_2
    
    def test_check_difficult_word(self, checker, token_factory):
        """Test difficulty check for difficult word."""
        token = token_factory('eloquent')
        difficulty = checker.check_word(token)
        
        assert difficulty.needs_ruby is True
        assert difficulty.ngsl_level == NGSLLevel.NOT_IN_NGSL
    
    def test_configure_thresholds(self, checker):
        """Test threshold configuration."""
        checker.configure(
            ngsl_threshold=2,
            cefr_threshold=CEFRLevel.A2,
            frequency_threshold=1000
        )
        
        assert checker.ngsl_threshold == 2
        assert checker.cefr_threshold == CEFRLevel.A2
        assert checker.frequency_threshold == 1000
    
    def test_pos_filter(self, checker, token_factory):
        """Test POS filtering."""
        checker.configure(pos_filter={'VERB'})
        
        noun_token = token_factory('book', pos='NOUN')
        verb_token = token_factory('read', pos='VERB')
        
        noun_diff = checker.check_word(noun_token)
        verb_diff = checker.check_word(verb_token)
        
        # Noun should not need ruby (filtered out)
        assert noun_diff.needs_ruby is False
    
    def test_proper_noun_exclusion(self, checker, token_factory):
        """Test proper noun exclusion."""
        checker.configure(exclude_proper_nouns=True)
        
        token = token_factory('Paris', pos='PROPN')
        difficulty = checker.check_word(token)
        
        assert difficulty.needs_ruby is False
    
    def test_filter_difficult_words(self, checker, token_factory):
        """Test filtering to only difficult words."""
        tokens = [
            token_factory('the'),
            token_factory('eloquent'),
            token_factory('book'),
            token_factory('ubiquitous')
        ]
        
        difficult = checker.filter_difficult_words(tokens)
        
        # Should only include difficult words
        words = [t.text.lower() for t, _ in difficult]
        assert 'eloquent' in words
        assert 'ubiquitous' in words
        assert 'the' not in words
    
    def test_statistics(self, checker, token_factory):
        """Test statistics generation."""
        tokens = [
            token_factory('the'),
            token_factory('eloquent'),
            token_factory('book')
        ]
        
        difficulties = checker.check_tokens(tokens)
        stats = checker.get_statistics(difficulties)
        
        assert 'total_words' in stats
        assert 'words_needing_ruby' in stats
        assert 'ruby_percentage' in stats
        assert stats['total_words'] == 3


class TestNGSLLevel:
    """Test cases for NGSLLevel enum."""
    
    def test_level_values(self):
        """Test NGSL level values."""
        assert NGSLLevel.LEVEL_1.value == 1
        assert NGSLLevel.LEVEL_2.value == 2
        assert NGSLLevel.LEVEL_3.value == 3
        assert NGSLLevel.NOT_IN_NGSL.value == 99
    
    def test_level_comparison(self):
        """Test level comparison."""
        assert NGSLLevel.LEVEL_1 < NGSLLevel.LEVEL_2
        assert NGSLLevel.LEVEL_3 < NGSLLevel.NOT_IN_NGSL


class TestCEFRLevel:
    """Test cases for CEFRLevel enum."""
    
    def test_level_values(self):
        """Test CEFR level values."""
        assert CEFRLevel.A1.value == 1
        assert CEFRLevel.B1.value == 3
        assert CEFRLevel.C2.value == 6
    
    def test_level_ordering(self):
        """Test CEFR level ordering."""
        assert CEFRLevel.A1 < CEFRLevel.A2 < CEFRLevel.B1
        assert CEFRLevel.B1 < CEFRLevel.B2 < CEFRLevel.C1 < CEFRLevel.C2


class TestWordDifficulty:
    """Test cases for WordDifficulty dataclass."""
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        difficulty = WordDifficulty(
            word='eloquent',
            lemma='eloquent',
            ngsl_level=NGSLLevel.NOT_IN_NGSL,
            cefr_level=CEFRLevel.C1,
            frequency_rank=15000,
            needs_ruby=True,
            pos='ADJ'
        )
        
        d = difficulty.to_dict()
        
        assert d['word'] == 'eloquent'
        assert d['needs_ruby'] is True
        assert d['ngsl_level'] == 99
        assert d['cefr_level'] == 5
