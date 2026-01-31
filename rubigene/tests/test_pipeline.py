"""
Tests for RubygenePipeline module.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from rubigene.core.pipeline import (
    RubygenePipeline,
    PipelineConfig,
    PipelineProgress,
    run_pipeline
)
from rubigene.core.difficulty_checker import CEFRLevel


class TestPipelineConfig:
    """Test cases for PipelineConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = PipelineConfig()
        
        assert config.ngsl_threshold == 3
        assert config.cefr_threshold == CEFRLevel.B1
        assert config.frequency_threshold == 3000
        assert config.include_nouns is True
        assert config.include_verbs is True
    
    def test_pos_filter_property(self):
        """Test POS filter set generation."""
        config = PipelineConfig(
            include_nouns=True,
            include_verbs=True,
            include_adjectives=False,
            include_adverbs=False
        )
        
        pos_filter = config.pos_filter
        
        assert 'NOUN' in pos_filter
        assert 'VERB' in pos_filter
        assert 'ADJ' not in pos_filter
        assert 'ADV' not in pos_filter
    
    def test_output_path_with_filename(self):
        """Test output path with explicit filename."""
        config = PipelineConfig(
            output_folder='/output',
            output_filename='test.ass'
        )
        
        assert config.output_path == '/output/test.ass'
    
    def test_output_path_auto_generated(self):
        """Test auto-generated output filename."""
        config = PipelineConfig(
            input_srt_path='/input/movie.srt',
            output_folder='/output'
        )
        
        assert config.output_path == '/output/movie_ruby.ass'


class TestPipelineProgress:
    """Test cases for PipelineProgress dataclass."""
    
    def test_percentage_calculation(self):
        """Test progress percentage calculation."""
        progress = PipelineProgress(
            stage='translate',
            current=50,
            total=100,
            message='Translating...'
        )
        
        assert progress.percentage == 50.0
    
    def test_percentage_zero_total(self):
        """Test percentage with zero total."""
        progress = PipelineProgress(
            stage='load',
            current=0,
            total=0,
            message='Loading...'
        )
        
        assert progress.percentage == 0


class TestRubygenePipeline:
    """Test cases for RubygenePipeline class."""
    
    @pytest.fixture
    def temp_srt(self):
        """Create temporary SRT file for testing."""
        content = """1
00:00:01,000 --> 00:00:04,000
The eloquent speaker impressed everyone.

2
00:00:05,000 --> 00:00:08,000
His ubiquitous presence was noted.
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.srt', delete=False, encoding='utf-8'
        ) as f:
            f.write(content)
            return f.name
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        config = PipelineConfig()
        pipeline = RubygenePipeline(config)
        
        assert pipeline.config is not None
        assert pipeline.entries == []
    
    def test_validate_config_missing_input(self):
        """Test validation with missing input file."""
        config = PipelineConfig(
            output_folder='/output',
            deepl_api_key='test-key'
        )
        pipeline = RubygenePipeline(config)
        
        with pytest.raises(ValueError, match='入力SRT'):
            pipeline._validate_config()
    
    def test_validate_config_missing_api_key(self, temp_srt, temp_output_dir):
        """Test validation with missing API key."""
        config = PipelineConfig(
            input_srt_path=temp_srt,
            output_folder=temp_output_dir
        )
        pipeline = RubygenePipeline(config)
        
        with pytest.raises(ValueError, match='APIキー'):
            pipeline._validate_config()
    
    def test_validate_config_file_not_found(self, temp_output_dir):
        """Test validation with non-existent file."""
        config = PipelineConfig(
            input_srt_path='/nonexistent/file.srt',
            output_folder=temp_output_dir,
            deepl_api_key='test-key'
        )
        pipeline = RubygenePipeline(config)
        
        with pytest.raises(FileNotFoundError):
            pipeline._validate_config()
    
    def test_progress_callback(self, temp_srt, temp_output_dir):
        """Test progress callback invocation."""
        config = PipelineConfig(
            input_srt_path=temp_srt,
            output_folder=temp_output_dir,
            deepl_api_key='test-key'
        )
        pipeline = RubygenePipeline(config)
        
        progress_messages = []
        
        def callback(progress):
            progress_messages.append(progress.message)
        
        pipeline.set_progress_callback(callback)
        
        # Mock the translation to avoid API calls
        with patch.object(pipeline, '_stage_translate'):
            try:
                pipeline.run()
            except Exception:
                pass  # Expected to fail at some point
        
        # Should have received some progress messages
        assert len(progress_messages) > 0
    
    def test_stage_load_srt(self, temp_srt, temp_output_dir):
        """Test SRT loading stage."""
        config = PipelineConfig(
            input_srt_path=temp_srt,
            output_folder=temp_output_dir,
            deepl_api_key='test-key'
        )
        pipeline = RubygenePipeline(config)
        pipeline.initialize_components()
        
        pipeline._stage_load_srt()
        
        assert len(pipeline.entries) == 2
        assert 'eloquent' in pipeline.entries[0].text
    
    def test_get_statistics(self, temp_srt, temp_output_dir):
        """Test statistics retrieval."""
        config = PipelineConfig(
            input_srt_path=temp_srt,
            output_folder=temp_output_dir,
            deepl_api_key='test-key'
        )
        pipeline = RubygenePipeline(config)
        pipeline.initialize_components()
        pipeline._stage_load_srt()
        
        stats = pipeline.get_statistics()
        
        assert 'subtitle_entries' in stats
        assert stats['subtitle_entries'] == 2


class TestRunPipeline:
    """Test cases for run_pipeline convenience function."""
    
    @pytest.fixture
    def temp_srt(self):
        """Create temporary SRT file."""
        content = """1
00:00:01,000 --> 00:00:04,000
Hello world.
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.srt', delete=False, encoding='utf-8'
        ) as f:
            f.write(content)
            return f.name
    
    def test_run_pipeline_creates_config(self, temp_srt):
        """Test that run_pipeline creates proper config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock pipeline to avoid actual execution
            with patch('rubigene.core.pipeline.RubygenePipeline') as MockPipeline:
                mock_instance = MagicMock()
                mock_instance.run.return_value = f'{tmpdir}/output.ass'
                MockPipeline.return_value = mock_instance
                
                result = run_pipeline(
                    input_srt=temp_srt,
                    output_folder=tmpdir,
                    api_key='test-key',
                    ngsl_threshold=2
                )
                
                # Verify pipeline was created with config
                MockPipeline.assert_called_once()
                config = MockPipeline.call_args[0][0]
                assert config.input_srt_path == temp_srt
                assert config.deepl_api_key == 'test-key'
                assert config.ngsl_threshold == 2
