"""
Tests for RubyTagGenerator module.
"""

import pytest
from rubigene.core.ruby_tag_generator import (
    RubyTagGenerator,
    RubyTag,
    create_ruby_text_simple
)
from rubigene.core.tokenizer import TokenInfo
from rubigene.core.difficulty_checker import WordDifficulty, NGSLLevel, CEFRLevel
from rubigene.core.translator import TranslationResult


class TestRubyTag:
    """Test cases for RubyTag dataclass."""
    
    def test_to_tag(self):
        """Test ruby tag string generation."""
        tag = RubyTag(
            original='eloquent',
            ruby='雄弁な',
            start_pos=0,
            end_pos=8
        )
        
        assert tag.to_tag() == 'r{eloquent|雄弁な}'
    
    def test_str_representation(self):
        """Test string representation."""
        tag = RubyTag(
            original='ubiquitous',
            ruby='至る所にある',
            start_pos=0,
            end_pos=10
        )
        
        assert str(tag) == 'r{ubiquitous|至る所にある}'


class TestRubyTagGenerator:
    """Test cases for RubyTagGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return RubyTagGenerator()
    
    @pytest.fixture
    def token_factory(self):
        """Factory for creating test tokens."""
        def create_token(text, start, end, lemma=None):
            return TokenInfo(
                text=text,
                lemma=lemma or text.lower(),
                pos='NOUN',
                tag='NN',
                is_stop=False,
                is_punct=False,
                is_alpha=True,
                is_digit=False,
                start_char=start,
                end_char=end
            )
        return create_token
    
    @pytest.fixture
    def difficulty_factory(self):
        """Factory for creating test difficulties."""
        def create_difficulty(word, needs_ruby=True):
            return WordDifficulty(
                word=word,
                lemma=word.lower(),
                ngsl_level=NGSLLevel.NOT_IN_NGSL,
                cefr_level=CEFRLevel.C1,
                frequency_rank=10000,
                needs_ruby=needs_ruby,
                pos='NOUN'
            )
        return create_difficulty
    
    def test_generate_ruby_text_single_word(
        self, generator, token_factory, difficulty_factory
    ):
        """Test ruby generation for single word."""
        text = "The eloquent speaker impressed everyone."
        token = token_factory('eloquent', 4, 12)
        difficulty = difficulty_factory('eloquent')
        
        translations = {
            'eloquent': TranslationResult('eloquent', '雄弁な')
        }
        
        result = generator.generate_ruby_text(
            text,
            [(token, difficulty)],
            translations
        )
        
        assert 'r{eloquent|雄弁な}' in result
        # Original structure preserved
        assert 'The' in result
        assert 'speaker' in result
    
    def test_generate_ruby_text_multiple_words(
        self, generator, token_factory, difficulty_factory
    ):
        """Test ruby generation for multiple words."""
        text = "The ubiquitous and eloquent leader."
        
        tokens_difficulties = [
            (token_factory('ubiquitous', 4, 14), difficulty_factory('ubiquitous')),
            (token_factory('eloquent', 19, 27), difficulty_factory('eloquent')),
        ]
        
        translations = {
            'ubiquitous': TranslationResult('ubiquitous', '至る所にある'),
            'eloquent': TranslationResult('eloquent', '雄弁な'),
        }
        
        result = generator.generate_ruby_text(
            text,
            tokens_difficulties,
            translations
        )
        
        assert 'r{ubiquitous|至る所にある}' in result
        assert 'r{eloquent|雄弁な}' in result
    
    def test_generate_empty_difficult_words(self, generator):
        """Test with no difficult words."""
        text = "The quick brown fox."
        
        result = generator.generate_ruby_text(text, [], {})
        
        assert result == text
    
    def test_generate_missing_translation(
        self, generator, token_factory, difficulty_factory
    ):
        """Test handling of missing translation."""
        text = "An eloquent speaker."
        token = token_factory('eloquent', 3, 11)
        difficulty = difficulty_factory('eloquent')
        
        # No translation provided
        translations = {}
        
        result = generator.generate_ruby_text(
            text,
            [(token, difficulty)],
            translations
        )
        
        # Original text preserved when no translation
        assert result == text
    
    def test_parse_ruby_tags(self, generator):
        """Test parsing ruby tags from text."""
        text = "The r{eloquent|雄弁な} speaker was r{ubiquitous|至る所にある}."
        
        tags = RubyTagGenerator.parse_ruby_tags(text)
        
        assert len(tags) == 2
        assert tags[0].original == 'eloquent'
        assert tags[0].ruby == '雄弁な'
        assert tags[1].original == 'ubiquitous'
    
    def test_strip_ruby_tags(self, generator):
        """Test stripping ruby tags."""
        text = "The r{eloquent|雄弁な} speaker."
        
        stripped = RubyTagGenerator.strip_ruby_tags(text)
        
        assert stripped == "The eloquent speaker."
        assert 'r{' not in stripped
    
    def test_extract_ruby_only(self, generator):
        """Test extracting only ruby text."""
        text = "The r{eloquent|雄弁な} speaker."
        
        ruby_only = RubyTagGenerator.extract_ruby_only(text)
        
        assert ruby_only == "The 雄弁な speaker."
    
    def test_get_statistics(
        self, generator, token_factory, difficulty_factory
    ):
        """Test statistics generation."""
        text = "The eloquent leader."
        token = token_factory('eloquent', 4, 12)
        difficulty = difficulty_factory('eloquent')
        
        translations = {
            'eloquent': TranslationResult('eloquent', '雄弁な')
        }
        
        generator.generate_ruby_text(
            text,
            [(token, difficulty)],
            translations
        )
        
        stats = generator.get_statistics()
        
        assert stats['total_tags'] == 1
        assert stats['unique_words'] == 1


class TestCreateRubyTextSimple:
    """Test cases for create_ruby_text_simple helper."""
    
    def test_simple_replacement(self):
        """Test simple word replacement."""
        text = "The eloquent speaker."
        translations = {'eloquent': '雄弁な'}
        
        result = create_ruby_text_simple(text, translations)
        
        assert 'r{eloquent|雄弁な}' in result
    
    def test_case_insensitive_replacement(self):
        """Test case-insensitive replacement."""
        text = "ELOQUENT speaker was Eloquent."
        translations = {'eloquent': '雄弁な'}
        
        result = create_ruby_text_simple(text, translations)
        
        # Both instances should be replaced preserving case
        assert 'r{ELOQUENT|雄弁な}' in result
        assert 'r{Eloquent|雄弁な}' in result
    
    def test_word_boundary_respect(self):
        """Test that only whole words are replaced."""
        text = "The reading is interesting."
        translations = {'read': '読む'}
        
        result = create_ruby_text_simple(text, translations)
        
        # 'reading' should not be affected
        assert 'reading' in result
        assert 'r{read' not in result
    
    def test_empty_translation(self):
        """Test handling of empty translation."""
        text = "The eloquent speaker."
        translations = {'eloquent': ''}
        
        result = create_ruby_text_simple(text, translations)
        
        # No replacement for empty translation
        assert result == text
    
    def test_multiple_words(self):
        """Test multiple word replacements."""
        text = "The eloquent and ubiquitous leader."
        translations = {
            'eloquent': '雄弁な',
            'ubiquitous': '至る所にある'
        }
        
        result = create_ruby_text_simple(text, translations)
        
        assert 'r{eloquent|雄弁な}' in result
        assert 'r{ubiquitous|至る所にある}' in result
