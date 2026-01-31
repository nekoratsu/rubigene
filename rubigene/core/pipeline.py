"""
Rubigene Processing Pipeline

Orchestrates the complete subtitle processing workflow from SRT to ASS.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
import logging

from .srt_loader import SRTLoader, SubtitleEntry
from .tokenizer import EnglishTokenizer, TokenInfo
from .difficulty_checker import DifficultyChecker, WordDifficulty, CEFRLevel
from .translator import DeepLTranslator, TranslationResult
from .ruby_tag_generator import RubyTagGenerator
from .rubysubs_wrapper import RubySubsGenerator

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the processing pipeline."""
    # Input/Output
    input_srt_path: str = ""
    output_folder: str = ""
    output_filename: Optional[str] = None
    
    # Difficulty thresholds
    ngsl_threshold: int = 3
    cefr_threshold: CEFRLevel = CEFRLevel.B1
    frequency_threshold: int = 3000
    
    # POS filters
    include_nouns: bool = True
    include_verbs: bool = True
    include_adjectives: bool = False
    include_adverbs: bool = False
    exclude_proper_nouns: bool = False
    
    # API settings
    deepl_api_key: str = ""
    
    # Output settings
    video_width: int = 1920
    video_height: int = 1080
    
    @property
    def pos_filter(self) -> Set[str]:
        """Get set of POS tags to include."""
        pos_set = set()
        if self.include_nouns:
            pos_set.add('NOUN')
        if self.include_verbs:
            pos_set.add('VERB')
        if self.include_adjectives:
            pos_set.add('ADJ')
        if self.include_adverbs:
            pos_set.add('ADV')
        return pos_set
    
    @property
    def output_path(self) -> str:
        """Get full output path for ASS file."""
        if self.output_filename:
            filename = self.output_filename
        else:
            input_path = Path(self.input_srt_path)
            filename = input_path.stem + "_ruby.ass"
        
        return str(Path(self.output_folder) / filename)


@dataclass
class PipelineProgress:
    """Progress information for pipeline execution."""
    stage: str
    current: int
    total: int
    message: str
    
    @property
    def percentage(self) -> float:
        """Get progress percentage."""
        return (self.current / self.total * 100) if self.total > 0 else 0


class RubygenePipeline:
    """
    Complete processing pipeline for Rubigene.
    
    Stages:
    1. Load SRT file
    2. Tokenize English text
    3. Evaluate word difficulty
    4. Translate difficult words
    5. Generate ruby tags
    6. Generate ASS output
    """
    
    STAGES = [
        ("load", "SRTを読み込み中"),
        ("tokenize", "英語の単語を解析中"),
        ("difficulty", "難易度を評価中"),
        ("translate", "DeepL翻訳中"),
        ("ruby_tags", "ルビタグを生成中"),
        ("generate_ass", "ASSを生成中"),
        ("complete", "完了")
    ]
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the pipeline.
        
        Args:
            config: Pipeline configuration.
        """
        self.config = config or PipelineConfig()
        
        # Components
        self.srt_loader: Optional[SRTLoader] = None
        self.tokenizer: Optional[EnglishTokenizer] = None
        self.difficulty_checker: Optional[DifficultyChecker] = None
        self.translator: Optional[DeepLTranslator] = None
        self.ruby_generator: Optional[RubyTagGenerator] = None
        self.ass_generator: Optional[RubySubsGenerator] = None
        
        # Results
        self.entries: List[SubtitleEntry] = []
        self.line_tokens: Dict[int, List[TokenInfo]] = {}
        self.line_difficulties: Dict[int, List[WordDifficulty]] = {}
        self.difficult_words: List[tuple] = []
        self.translations: Dict[str, TranslationResult] = {}
        self.ruby_texts: List[str] = []
        
        # Progress callback
        self._progress_callback: Optional[Callable[[PipelineProgress], None]] = None
    
    def set_progress_callback(
        self,
        callback: Callable[[PipelineProgress], None]
    ) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback
    
    def _report_progress(
        self,
        stage: str,
        current: int,
        total: int,
        message: str = ""
    ) -> None:
        """Report progress to callback."""
        if self._progress_callback:
            progress = PipelineProgress(
                stage=stage,
                current=current,
                total=total,
                message=message
            )
            self._progress_callback(progress)
    
    def _get_stage_message(self, stage: str) -> str:
        """Get localized message for stage."""
        for s, msg in self.STAGES:
            if s == stage:
                return msg
        return stage
    
    def configure(self, config: PipelineConfig) -> None:
        """Update pipeline configuration."""
        self.config = config
    
    def initialize_components(self) -> None:
        """Initialize all pipeline components."""
        logger.info("Initializing pipeline components")
        
        # SRT Loader
        self.srt_loader = SRTLoader()
        
        # Tokenizer
        self.tokenizer = EnglishTokenizer()
        
        # Difficulty Checker
        self.difficulty_checker = DifficultyChecker()
        self.difficulty_checker.configure(
            ngsl_threshold=self.config.ngsl_threshold,
            cefr_threshold=self.config.cefr_threshold,
            frequency_threshold=self.config.frequency_threshold,
            pos_filter=self.config.pos_filter,
            exclude_proper_nouns=self.config.exclude_proper_nouns
        )
        
        # Translator
        self.translator = DeepLTranslator(api_key=self.config.deepl_api_key)
        
        # Ruby Tag Generator
        self.ruby_generator = RubyTagGenerator()
        
        # ASS Generator
        self.ass_generator = RubySubsGenerator(
            video_width=self.config.video_width,
            video_height=self.config.video_height
        )
    
    def run(self) -> str:
        """
        Run the complete pipeline.
        
        Returns:
            Path to generated ASS file.
            
        Raises:
            ValueError: If configuration is invalid.
            FileNotFoundError: If input file doesn't exist.
            Exception: On processing errors.
        """
        # Validate configuration
        self._validate_config()
        
        # Initialize components
        self.initialize_components()
        
        total_stages = len(self.STAGES)
        
        try:
            # Stage 1: Load SRT
            self._report_progress("load", 1, total_stages, "SRTを読み込み中…")
            self._stage_load_srt()
            
            # Stage 2: Tokenize
            self._report_progress("tokenize", 2, total_stages, "英語の単語を解析中…")
            self._stage_tokenize()
            
            # Stage 3: Difficulty evaluation
            self._report_progress("difficulty", 3, total_stages, "難易度を評価中…")
            self._stage_difficulty()
            
            # Stage 4: Translation
            self._report_progress("translate", 4, total_stages, "DeepL翻訳中…")
            self._stage_translate()
            
            # Stage 5: Ruby tags
            self._report_progress("ruby_tags", 5, total_stages, "ルビタグを生成中…")
            self._stage_ruby_tags()
            
            # Stage 6: Generate ASS
            self._report_progress("generate_ass", 6, total_stages, "ASSを生成中…")
            self._stage_generate_ass()
            
            # Complete
            self._report_progress("complete", 7, total_stages, "完了しました！")
            
            logger.info(f"Pipeline completed: {self.config.output_path}")
            return self.config.output_path
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
    
    def _validate_config(self) -> None:
        """Validate pipeline configuration."""
        if not self.config.input_srt_path:
            raise ValueError("入力SRTファイルが指定されていません")
        
        if not Path(self.config.input_srt_path).exists():
            raise FileNotFoundError(
                f"SRTファイルが見つかりません: {self.config.input_srt_path}"
            )
        
        if not self.config.output_folder:
            raise ValueError("出力フォルダが指定されていません")
        
        if not self.config.deepl_api_key:
            raise ValueError("DeepL APIキーが設定されていません")
    
    def _stage_load_srt(self) -> None:
        """Stage 1: Load SRT file."""
        self.entries = self.srt_loader.load(self.config.input_srt_path)
        logger.info(f"Loaded {len(self.entries)} subtitle entries")
    
    def _stage_tokenize(self) -> None:
        """Stage 2: Tokenize English text."""
        texts = [entry.text for entry in self.entries]
        
        for i, text in enumerate(texts):
            tokens = self.tokenizer.tokenize_clean(text)
            self.line_tokens[i] = tokens
        
        logger.info(f"Tokenized {len(texts)} lines")
    
    def _stage_difficulty(self) -> None:
        """Stage 3: Evaluate word difficulty."""
        all_difficult = []
        print("[DEBUG] --- 難易度判定 ---")
        for i, tokens in self.line_tokens.items():
            difficulties = self.difficulty_checker.check_tokens(tokens)
            self.line_difficulties[i] = difficulties
            print(f"[DEBUG] line {i}: tokens = {[t.text for t in tokens]}")
            print(f"[DEBUG] line {i}: needs_ruby = {[d.needs_ruby for d in difficulties]}")
            # Collect difficult words
            for token, diff in zip(tokens, difficulties):
                if diff.needs_ruby:
                    print(f"[DEBUG] ルビ対象: {token.text} (lemma={token.lemma})")
                    all_difficult.append((token, diff))
        self.difficult_words = all_difficult
        logger.info(f"Found {len(all_difficult)} words needing ruby")
    
    def _stage_translate(self) -> None:
        """Stage 4: Translate difficult words."""
        # Get unique words to translate
        words_to_translate = list(set(
            token.lemma.lower() for token, _ in self.difficult_words
        ))
        print("[DEBUG] --- 翻訳対象単語 ---")
        print(words_to_translate)
        def translation_progress(current, total, word):
            msg = f"翻訳中: {word} ({current}/{total})"
            self._report_progress("translate", 4, len(self.STAGES), msg)
        self.translations = self.translator.translate_batch(
            words_to_translate,
            progress_callback=translation_progress
        )
        print("[DEBUG] --- 翻訳結果 ---")
        for k, v in self.translations.items():
            print(f"[DEBUG] {k} => {v.translation} (error={getattr(v, 'error', None)})")
        logger.info(f"Translated {len(self.translations)} unique words")
    
    def _stage_ruby_tags(self) -> None:
        """Stage 5: Generate ruby tags."""
        texts = [entry.text for entry in self.entries]
        self.ruby_texts = self.ruby_generator.batch_generate(
            texts,
            self.line_tokens,
            self.line_difficulties,
            self.translations
        )
        print("[DEBUG] --- ルビタグ生成結果 ---")
        for i, line in enumerate(self.ruby_texts):
            print(f"[DEBUG] ruby_texts[{i}]: {line}")
        logger.info(f"Generated ruby tags for {len(self.ruby_texts)} lines")
    
    def _stage_generate_ass(self) -> None:
        """Stage 6: Generate ASS file."""
        # Ensure output directory exists
        output_dir = Path(self.config.output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.ass_generator.save_ass(
            self.config.output_path,
            self.entries,
            self.ruby_texts
        )
        
        logger.info(f"Generated ASS: {self.config.output_path}")
    
    def get_statistics(self) -> Dict:
        """Get processing statistics."""
        return {
            'subtitle_entries': len(self.entries),
            'total_tokens': sum(len(t) for t in self.line_tokens.values()),
            'difficult_words': len(self.difficult_words),
            'unique_translations': len(self.translations),
            'cached_translations': sum(
                1 for t in self.translations.values() if t.cached
            ),
            'api_translations': sum(
                1 for t in self.translations.values() if not t.cached
            )
        }


def run_pipeline(
    input_srt: str,
    output_folder: str,
    api_key: str,
    progress_callback: Optional[Callable] = None,
    **kwargs
) -> str:
    """
    Convenience function to run the pipeline.
    
    Args:
        input_srt: Path to input SRT file.
        output_folder: Path to output folder.
        api_key: DeepL API key.
        progress_callback: Optional progress callback.
        **kwargs: Additional configuration options.
        
    Returns:
        Path to generated ASS file.
    """
    config = PipelineConfig(
        input_srt_path=input_srt,
        output_folder=output_folder,
        deepl_api_key=api_key,
        **kwargs
    )
    
    pipeline = RubygenePipeline(config)
    
    if progress_callback:
        pipeline.set_progress_callback(progress_callback)
    
    return pipeline.run()
