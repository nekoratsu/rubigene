"""
DeepL Translator Module

Translates English words to Japanese using DeepL API with caching.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import urllib.request
import urllib.error
import urllib.parse

from .utils import get_data_path


@dataclass
class TranslationResult:
    """Result of a translation request."""
    source: str
    translation: str
    cached: bool = False
    error: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if translation is valid."""
        return self.error is None and bool(self.translation)


class TranslationCache:
    """
    Persistent cache for translations to reduce API calls.
    """
    
    def __init__(self, cache_path: Optional[str] = None):
        """
        Initialize translation cache.
        
        Args:
            cache_path: Path to cache JSON file.
        """
        self.cache_path = Path(
            cache_path or get_data_path('translation_cache.json')
        )
        self.cache: Dict[str, str] = {}
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from file."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.cache = {}
    
    def save(self) -> None:
        """Save cache to file."""
        # Ensure parent directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def get(self, word: str) -> Optional[str]:
        """Get cached translation for a word."""
        return self.cache.get(word.lower())
    
    def set(self, word: str, translation: str) -> None:
        """Cache a translation."""
        self.cache[word.lower()] = translation
    
    def has(self, word: str) -> bool:
        """Check if word is in cache."""
        return word.lower() in self.cache
    
    def clear(self) -> None:
        """Clear all cached translations."""
        self.cache = {}
        self.save()
    
    def __len__(self) -> int:
        """Return number of cached translations."""
        return len(self.cache)


class DeepLTranslator:
    """
    Translates English words to Japanese using DeepL API.
    
    Features:
    - Translation caching for efficiency
    - Batch translation support
    - Rate limiting
    - Error handling
    """
    
    # DeepL API endpoints
    API_URL_FREE = "https://api-free.deepl.com/v2/translate"
    API_URL_PRO = "https://api.deepl.com/v2/translate"
    
    # Rate limiting
    MIN_REQUEST_INTERVAL = 0.05  # 50ms between requests
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_path: Optional[str] = None,
        use_pro_api: bool = False
    ):
        """
        Initialize DeepL translator.
        
        Args:
            api_key: DeepL API key.
            cache_path: Path to translation cache file.
            use_pro_api: Use Pro API endpoint (default: Free).
        """
        self.api_key = api_key
        self.cache = TranslationCache(cache_path)
        self.api_url = self.API_URL_PRO if use_pro_api else self.API_URL_FREE
        self._last_request_time = 0.0
    
    def set_api_key(self, api_key: str) -> None:
        """Set or update API key."""
        self.api_key = api_key
    
    def translate_word(self, word: str) -> TranslationResult:
        """
        Translate a single English word to Japanese.
        
        Args:
            word: English word to translate.
            
        Returns:
            TranslationResult with translation.
        """
        # Check cache first
        cached = self.cache.get(word)
        if cached:
            return TranslationResult(
                source=word,
                translation=cached,
                cached=True
            )
        
        # Check API key
        if not self.api_key:
            return TranslationResult(
                source=word,
                translation="",
                error="APIキーが設定されていません"
            )
        
        # Rate limiting
        self._apply_rate_limit()
        
        # Make API request
        try:
            translation = self._call_deepl_api(word)
            
            # Cache the result
            self.cache.set(word, translation)
            self.cache.save()
            
            return TranslationResult(
                source=word,
                translation=translation,
                cached=False
            )
            
        except Exception as e:
            return TranslationResult(
                source=word,
                translation="",
                error=str(e)
            )
    
    def translate_batch(
        self,
        words: List[str],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, TranslationResult]:
        """
        Translate multiple words with progress tracking.
        
        Args:
            words: List of English words to translate.
            progress_callback: Optional callback(current, total, word).
            
        Returns:
            Dictionary mapping words to TranslationResults.
        """
        results = {}
        total = len(words)
        
        # Deduplicate while preserving order
        unique_words = list(dict.fromkeys(word.lower() for word in words))
        
        for i, word in enumerate(unique_words):
            result = self.translate_word(word)
            results[word] = result
            
            if progress_callback:
                progress_callback(i + 1, len(unique_words), word)
        
        return results
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()
    
    def _call_deepl_api(self, text: str) -> str:
        """
        Make DeepL API translation request (curl互換: Authorizationヘッダー認証)。
        Args:
            text: Text to translate.
        Returns:
            Translated text.
        Raises:
            Exception on API error.
        """
        # Prepare request data (auth_keyはbodyに含めない)
        data = urllib.parse.urlencode({
            'text': text,
            'source_lang': 'EN',
            'target_lang': 'JA'
        }).encode('utf-8')

        # Create request with Authorization header
        request = urllib.request.Request(
            self.api_url,
            data=data,
            method='POST'
        )
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        request.add_header('Authorization', f'DeepL-Auth-Key {self.api_key}')

        # Make request
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                translations = result.get('translations', [])
                if translations:
                    return translations[0].get('text', '')
                return ''
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            if e.code == 403:
                raise Exception("APIキーが無効です")
            elif e.code == 429:
                raise Exception("API制限に達しました。しばらく待ってください")
            elif e.code == 456:
                raise Exception("翻訳クォータを超過しました")
            else:
                raise Exception(f"API エラー ({e.code}): {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"接続エラー: {e.reason}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            'cached_words': len(self.cache),
            'cache_path': str(self.cache.cache_path)
        }
    
    def validate_api_key(self) -> Tuple[bool, str]:
        """
        Validate the current API key.
        
        Returns:
            Tuple of (is_valid, message).
        """
        if not self.api_key:
            return False, "APIキーが設定されていません"
        
        try:
            # Try a simple translation to validate key
            result = self._call_deepl_api("hello")
            if result:
                return True, "APIキーは有効です"
            return False, "APIからの応答がありません"
        except Exception as e:
            return False, str(e)
    
    def clear_cache(self) -> None:
        """Clear translation cache."""
        self.cache.clear()
