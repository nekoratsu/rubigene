"""
Tests for DeepLTranslator module.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from rubigene.core.translator import (
    DeepLTranslator,
    TranslationCache,
    TranslationResult
)


class TestTranslationCache:
    """Test cases for TranslationCache class."""
    
    @pytest.fixture
    def temp_cache_file(self):
        """Create temporary cache file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump({'hello': 'こんにちは', 'world': '世界'}, f)
            return f.name
    
    def test_load_existing_cache(self, temp_cache_file):
        """Test loading existing cache file."""
        cache = TranslationCache(temp_cache_file)
        
        assert cache.get('hello') == 'こんにちは'
        assert cache.get('world') == '世界'
    
    def test_cache_miss(self, temp_cache_file):
        """Test cache miss returns None."""
        cache = TranslationCache(temp_cache_file)
        
        assert cache.get('unknown') is None
    
    def test_set_and_get(self, temp_cache_file):
        """Test setting and getting cache values."""
        cache = TranslationCache(temp_cache_file)
        
        cache.set('test', 'テスト')
        assert cache.get('test') == 'テスト'
    
    def test_case_insensitive(self, temp_cache_file):
        """Test cache is case-insensitive."""
        cache = TranslationCache(temp_cache_file)
        
        cache.set('Test', 'テスト')
        assert cache.get('test') == 'テスト'
        assert cache.get('TEST') == 'テスト'
    
    def test_save_cache(self):
        """Test saving cache to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'cache.json'
            cache = TranslationCache(str(cache_path))
            
            cache.set('apple', 'りんご')
            cache.save()
            
            # Verify file was written
            assert cache_path.exists()
            with open(cache_path) as f:
                data = json.load(f)
                assert data['apple'] == 'りんご'
    
    def test_clear_cache(self, temp_cache_file):
        """Test clearing cache."""
        cache = TranslationCache(temp_cache_file)
        cache.clear()
        
        assert len(cache) == 0
        assert cache.get('hello') is None
    
    def test_has_method(self, temp_cache_file):
        """Test has() method."""
        cache = TranslationCache(temp_cache_file)
        
        assert cache.has('hello') is True
        assert cache.has('unknown') is False


class TestTranslationResult:
    """Test cases for TranslationResult dataclass."""
    
    def test_valid_result(self):
        """Test valid translation result."""
        result = TranslationResult(
            source='hello',
            translation='こんにちは',
            cached=False
        )
        
        assert result.is_valid is True
        assert result.source == 'hello'
        assert result.translation == 'こんにちは'
    
    def test_error_result(self):
        """Test error translation result."""
        result = TranslationResult(
            source='hello',
            translation='',
            error='API error'
        )
        
        assert result.is_valid is False
        assert result.error == 'API error'
    
    def test_cached_result(self):
        """Test cached translation result."""
        result = TranslationResult(
            source='hello',
            translation='こんにちは',
            cached=True
        )
        
        assert result.cached is True


class TestDeepLTranslator:
    """Test cases for DeepLTranslator class."""
    
    @pytest.fixture
    def translator(self):
        """Create translator with test API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'cache.json'
            return DeepLTranslator(
                api_key='test-api-key',
                cache_path=str(cache_path)
            )
    
    def test_translate_from_cache(self, translator):
        """Test translation from cache."""
        # Pre-populate cache
        translator.cache.set('hello', 'こんにちは')
        
        result = translator.translate_word('hello')
        
        assert result.is_valid
        assert result.cached is True
        assert result.translation == 'こんにちは'
    
    def test_translate_no_api_key(self):
        """Test translation without API key."""
        translator = DeepLTranslator(api_key=None)
        
        result = translator.translate_word('hello')
        
        assert result.is_valid is False
        assert 'APIキー' in result.error
    
    @patch('urllib.request.urlopen')
    def test_translate_api_call(self, mock_urlopen, translator):
        """Test API call for translation."""
        # Mock API response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            'translations': [{'text': 'こんにちは'}]
        }).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        result = translator.translate_word('hello')
        
        assert result.is_valid
        assert result.translation == 'こんにちは'
        assert result.cached is False
    
    @patch('urllib.request.urlopen')
    def test_translate_batch(self, mock_urlopen, translator):
        """Test batch translation."""
        # Pre-populate cache for one word
        translator.cache.set('hello', 'こんにちは')
        
        # Mock API response for uncached word
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            'translations': [{'text': '世界'}]
        }).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        results = translator.translate_batch(['hello', 'world'])
        
        assert 'hello' in results
        assert 'world' in results
        assert results['hello'].cached is True
        assert results['world'].cached is False
    
    @patch('urllib.request.urlopen')
    def test_api_error_handling(self, mock_urlopen, translator):
        """Test API error handling."""
        import urllib.error
        
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url='', code=403, msg='Forbidden', hdrs={}, fp=None
        )
        
        result = translator.translate_word('hello')
        
        assert result.is_valid is False
        assert 'APIキー' in result.error or '無効' in result.error
    
    def test_get_cache_stats(self, translator):
        """Test cache statistics."""
        translator.cache.set('word1', '単語1')
        translator.cache.set('word2', '単語2')
        
        stats = translator.get_cache_stats()
        
        assert stats['cached_words'] == 2
        assert 'cache_path' in stats
    
    def test_set_api_key(self, translator):
        """Test setting API key."""
        translator.set_api_key('new-api-key')
        
        assert translator.api_key == 'new-api-key'
