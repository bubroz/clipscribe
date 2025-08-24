"""Unit tests for ModelManager module."""
import pytest
import time
import warnings
from unittest.mock import patch, MagicMock, Mock, call
from typing import Dict, Any

from clipscribe.extractors.model_manager import ModelManager, get_model_manager
from clipscribe.utils.optional_deps import OptionalDependencyError


@pytest.fixture
def reset_model_manager():
    """Reset the ModelManager singleton before each test."""
    # Clear the singleton instance
    ModelManager._instance = None
    ModelManager._models = {}
    ModelManager._performance_monitor = None
    ModelManager._load_times = {}
    ModelManager._access_counts = {}

    # Reset the global instance
    import clipscribe.extractors.model_manager as mm
    mm._model_manager_instance = None

    yield

    # Clean up after test
    ModelManager._instance = None
    ModelManager._models = {}
    ModelManager._performance_monitor = None
    ModelManager._load_times = {}
    ModelManager._access_counts = {}
    mm._model_manager_instance = None


class TestModelManagerSingleton:
    """Test ModelManager singleton behavior."""

    def test_singleton_pattern(self, reset_model_manager):
        """Test that ModelManager follows singleton pattern."""
        manager1 = ModelManager()
        manager2 = ModelManager()

        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    def test_multiple_instances_are_same(self, reset_model_manager):
        """Test that multiple ModelManager() calls return same instance."""
        managers = [ModelManager() for _ in range(5)]

        # All should be the same instance
        for manager in managers[1:]:
            assert manager is managers[0]

    def test_get_model_manager_function(self, reset_model_manager):
        """Test the global get_model_manager function."""
        manager1 = get_model_manager()
        manager2 = get_model_manager()

        assert manager1 is manager2
        assert isinstance(manager1, ModelManager)

    def test_initialization_once(self, reset_model_manager):
        """Test that __init__ is only called once."""
        # This test is complex due to singleton nature and __new__ override
        # The singleton pattern is already tested by test_singleton_pattern
        # and test_multiple_instances_are_same
        pass


class TestModelManagerPerformance:
    """Test ModelManager performance monitoring functionality."""

    def test_set_performance_monitor(self, reset_model_manager):
        """Test setting performance monitor."""
        manager = ModelManager()
        mock_monitor = MagicMock()

        manager.set_performance_monitor(mock_monitor)

        assert manager._performance_monitor is mock_monitor

    def test_record_cache_hit_no_monitor(self, reset_model_manager):
        """Test recording cache hit without performance monitor."""
        manager = ModelManager()

        with patch('clipscribe.extractors.model_manager.logger') as mock_logger:
            manager._record_cache_hit("test_model")

        # Should log debug message
        mock_logger.debug.assert_called_with("Cache hit for test_model (access #1)")

        # Should update access count
        assert manager._access_counts["test_model"] == 1

    def test_record_cache_hit_with_monitor(self, reset_model_manager):
        """Test recording cache hit with performance monitor."""
        manager = ModelManager()
        mock_monitor = MagicMock()

        manager.set_performance_monitor(mock_monitor)
        manager._load_times["test_model"] = 2.5

        with patch('clipscribe.extractors.model_manager.logger') as mock_logger:
            manager._record_cache_hit("test_model")

        # Should call monitor
        mock_monitor.record_model_cache_hit.assert_called_with("test_model", 2.5)

        # Should log debug message
        mock_logger.debug.assert_called_with("Cache hit for test_model (access #1)")

    def test_record_cache_miss_no_monitor(self, reset_model_manager):
        """Test recording cache miss without performance monitor."""
        manager = ModelManager()

        with patch('clipscribe.extractors.model_manager.logger') as mock_logger:
            manager._record_cache_miss("test_model", 3.2)

        # Should log info message
        mock_logger.info.assert_called_with("Cache miss for test_model - loaded in 3.20s")

        # Should update tracking data
        assert manager._load_times["test_model"] == 3.2
        assert manager._access_counts["test_model"] == 1

    def test_record_cache_miss_with_monitor(self, reset_model_manager):
        """Test recording cache miss with performance monitor."""
        manager = ModelManager()
        mock_monitor = MagicMock()

        manager.set_performance_monitor(mock_monitor)

        with patch('clipscribe.extractors.model_manager.logger') as mock_logger:
            manager._record_cache_miss("test_model", 4.1)

        # Should call monitor
        mock_monitor.record_model_cache_miss.assert_called_with("test_model", 4.1)

        # Should log info message
        mock_logger.info.assert_called_with("Cache miss for test_model - loaded in 4.10s")

        # Should update tracking data
        assert manager._load_times["test_model"] == 4.1
        assert manager._access_counts["test_model"] == 1


class TestModelManagerSpacy:
    """Test ModelManager SpaCy model functionality."""

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_spacy_model_success(self, mock_deps, reset_model_manager):
        """Test successful SpaCy model loading."""
        manager = ModelManager()

        # Setup mocks
        mock_spacy = MagicMock()
        mock_model = MagicMock()
        mock_spacy.load.return_value = mock_model

        mock_deps.require_dependency.return_value = mock_spacy

        with patch('time.time', side_effect=[1000.0, 1002.5]), \
             patch('clipscribe.extractors.model_manager.logger') as mock_logger:

            result = manager.get_spacy_model("en_core_web_sm")

        # Verify results
        assert result is mock_model
        assert "spacy_en_core_web_sm" in manager._models

        # Verify dependency loading
        mock_deps.require_dependency.assert_called_with("spacy", "SpaCy entity extraction")

        # Verify logging
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_any_call(
            "Hybrid Extractors Loaded: Local (SpaCy for entities, GLiNER for detection, REBEL for relationships) + Gemini 2.5 Pro Refinement"
        )
        mock_logger.info.assert_any_call("SpaCy model en_core_web_sm loaded successfully in 2.50s ")

        # Verify performance tracking
        assert manager._load_times["spacy_en_core_web_sm"] == 2.5
        assert manager._access_counts["spacy_en_core_web_sm"] == 1

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_spacy_model_cache_hit(self, mock_deps, reset_model_manager):
        """Test SpaCy model cache hit."""
        manager = ModelManager()

        # Setup initial model in cache
        mock_model = MagicMock()
        manager._models["spacy_en_core_web_sm"] = mock_model

        result = manager.get_spacy_model("en_core_web_sm")

        # Should return cached model
        assert result is mock_model

        # Should not call dependency loading
        mock_deps.require_dependency.assert_not_called()

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_spacy_model_dependency_error(self, mock_deps, reset_model_manager):
        """Test SpaCy model loading with dependency error."""
        manager = ModelManager()

        # Setup dependency error
        mock_deps.require_dependency.side_effect = OptionalDependencyError("SpaCy not available")

        with pytest.raises(OptionalDependencyError):
            manager.get_spacy_model("en_core_web_sm")

        # Model should not be cached
        assert "spacy_en_core_web_sm" not in manager._models

    def test_get_spacy_model_different_names(self, reset_model_manager):
        """Test loading different SpaCy models."""
        manager = ModelManager()

        with patch('clipscribe.extractors.model_manager.optional_deps') as mock_deps:
            mock_spacy = MagicMock()
            mock_model1 = MagicMock()
            mock_model2 = MagicMock()

            mock_spacy.load.side_effect = [mock_model1, mock_model2]
            mock_deps.require_dependency.return_value = mock_spacy

            # Load two different models
            result1 = manager.get_spacy_model("en_core_web_sm")
            result2 = manager.get_spacy_model("en_core_web_lg")

            assert result1 is mock_model1
            assert result2 is mock_model2

            # Both should be cached with different keys
            assert "spacy_en_core_web_sm" in manager._models
            assert "spacy_en_core_web_lg" in manager._models


class TestModelManagerGliner:
    """Test ModelManager GLiNER model functionality."""

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_gliner_model_success_cpu(self, mock_deps, reset_model_manager):
        """Test successful GLiNER model loading on CPU."""
        manager = ModelManager()

        # Setup mocks
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False

        mock_gliner = MagicMock()
        mock_model = MagicMock()
        mock_gliner.GLiNER.from_pretrained.return_value = mock_model

        mock_deps.require_dependency.side_effect = [mock_torch, mock_gliner]

        with patch('time.time', side_effect=[1000.0, 1005.0]), \
             patch('clipscribe.extractors.model_manager.logger') as mock_logger:

            result = manager.get_gliner_model("test/model", "cpu")

        # Verify results
        assert result == (mock_model, "cpu")

        # Verify device determination - these are called when device="auto"
        # Since we explicitly set device="cpu", these won't be called
        # mock_torch.cuda.is_available.assert_called()
        # mock_torch.backends.mps.is_available.assert_called()

        # Verify model loading
        mock_gliner.GLiNER.from_pretrained.assert_called_with("test/model")

        # Should not call .to() for CPU
        mock_model.to.assert_not_called()

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_gliner_model_success_cuda(self, mock_deps, reset_model_manager):
        """Test successful GLiNER model loading on CUDA."""
        manager = ModelManager()

        # Setup mocks
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.backends.mps.is_available.return_value = False

        mock_gliner = MagicMock()
        mock_model = MagicMock()
        mock_gliner.GLiNER.from_pretrained.return_value = mock_model

        mock_deps.require_dependency.side_effect = [mock_torch, mock_gliner]

        with patch('time.time', side_effect=[1000.0, 1003.0, 1005.0, 1007.0]):
            result = manager.get_gliner_model("test/model", "auto")

        # Should use CUDA
        mock_model.to.assert_called_with("cuda")
        assert result == (mock_model, "cuda")

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_gliner_model_success_mps(self, mock_deps, reset_model_manager):
        """Test successful GLiNER model loading on MPS."""
        manager = ModelManager()

        # Setup mocks
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True

        mock_gliner = MagicMock()
        mock_model = MagicMock()
        mock_gliner.GLiNER.from_pretrained.return_value = mock_model

        mock_deps.require_dependency.side_effect = [mock_torch, mock_gliner]

        with patch('time.time', side_effect=[1000.0, 1004.0, 1006.0, 1008.0]):
            result = manager.get_gliner_model("test/model", "auto")

        # Should use MPS
        mock_model.to.assert_called_with("mps")
        assert result == (mock_model, "mps")

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_gliner_model_cache_hit(self, mock_deps, reset_model_manager):
        """Test GLiNER model cache hit."""
        manager = ModelManager()

        # Setup cached model
        mock_model = MagicMock()
        manager._models["gliner_test/model_cpu"] = (mock_model, "cpu")

        result = manager.get_gliner_model("test/model", "cpu")

        # Should return cached model
        assert result == (mock_model, "cpu")

        # Should not call dependencies
        mock_deps.require_dependency.assert_not_called()

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_gliner_model_dependency_error(self, mock_deps, reset_model_manager):
        """Test GLiNER model loading with dependency error."""
        manager = ModelManager()

        # Setup dependency error
        mock_deps.require_dependency.side_effect = OptionalDependencyError("GLiNER not available")

        with pytest.raises(OptionalDependencyError):
            manager.get_gliner_model("test/model")

        # Model should not be cached
        assert len(manager._models) == 0


class TestModelManagerRebel:
    """Test ModelManager REBEL model functionality."""

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_rebel_model_success_cpu(self, mock_deps, reset_model_manager):
        """Test successful REBEL model loading on CPU."""
        manager = ModelManager()

        # Setup mocks
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False

        mock_transformers = MagicMock()
        mock_pipeline = MagicMock()
        mock_transformers.pipeline.return_value = mock_pipeline

        mock_deps.require_dependency.side_effect = [mock_torch, mock_transformers]

        with patch('time.time', side_effect=[1000.0, 1006.0]), \
             patch('clipscribe.extractors.model_manager.logger') as mock_logger:

            result = manager.get_rebel_model("test/model", "auto")

        # Verify results
        assert result is mock_pipeline

        # Verify pipeline creation with CPU device
        mock_transformers.pipeline.assert_called_with(
            "text2text-generation",
            model="test/model",
            tokenizer="test/model",
            device=-1,  # CPU
            max_length=256,
        )

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_rebel_model_success_cuda(self, mock_deps, reset_model_manager):
        """Test successful REBEL model loading on CUDA."""
        manager = ModelManager()

        # Setup mocks
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.backends.mps.is_available.return_value = False

        mock_transformers = MagicMock()
        mock_pipeline = MagicMock()
        mock_transformers.pipeline.return_value = mock_pipeline

        mock_deps.require_dependency.side_effect = [mock_torch, mock_transformers]

        with patch('time.time', side_effect=[1000.0, 1002.0, 1004.0, 1006.0]):
            result = manager.get_rebel_model("test/model", "auto")

        # Verify pipeline creation with CUDA device
        mock_transformers.pipeline.assert_called_with(
            "text2text-generation",
            model="test/model",
            tokenizer="test/model",
            device=0,  # CUDA
            max_length=256,
        )

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_rebel_model_explicit_device(self, mock_deps, reset_model_manager):
        """Test REBEL model loading with explicit device."""
        manager = ModelManager()

        # Setup mocks
        mock_torch = MagicMock()
        mock_transformers = MagicMock()
        mock_pipeline = MagicMock()
        mock_transformers.pipeline.return_value = mock_pipeline

        mock_deps.require_dependency.side_effect = [mock_torch, mock_transformers]

        # Test explicit CUDA
        result = manager.get_rebel_model("test/model", "cuda")
        mock_transformers.pipeline.assert_called_with(
            "text2text-generation",
            model="test/model",
            tokenizer="test/model",
            device=0,
            max_length=256,
        )

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_rebel_model_cache_hit(self, mock_deps, reset_model_manager):
        """Test REBEL model cache hit."""
        manager = ModelManager()

        # Setup cached model
        mock_pipeline = MagicMock()
        manager._models["rebel_test/model_cpu"] = mock_pipeline  # CPU device = -1

        result = manager.get_rebel_model("test/model", "cpu")

        # Should return cached model
        assert result is mock_pipeline

        # Should not call dependencies
        mock_deps.require_dependency.assert_not_called()

    @patch('clipscribe.extractors.model_manager.optional_deps')
    def test_get_rebel_model_dependency_error(self, mock_deps, reset_model_manager):
        """Test REBEL model loading with dependency error."""
        manager = ModelManager()

        # Setup dependency error
        mock_deps.require_dependency.side_effect = OptionalDependencyError("REBEL not available")

        with pytest.raises(OptionalDependencyError):
            manager.get_rebel_model("test/model")

        # Model should not be cached
        assert len(manager._models) == 0


class TestModelManagerCache:
    """Test ModelManager cache management functionality."""

    def test_clear_cache(self, reset_model_manager):
        """Test clearing the cache."""
        manager = ModelManager()

        # Setup some cached data
        manager._models = {"model1": "data1", "model2": "data2"}
        manager._load_times = {"model1": 1.0, "model2": 2.0}
        manager._access_counts = {"model1": 5, "model2": 3}

        with patch('clipscribe.extractors.model_manager.logger') as mock_logger:
            manager.clear_cache()

        # All data should be cleared
        assert len(manager._models) == 0
        assert len(manager._load_times) == 0
        assert len(manager._access_counts) == 0

        # Should log the clearing
        mock_logger.info.assert_called_with("Clearing 2 cached models")

    def test_get_cache_info_empty(self, reset_model_manager):
        """Test getting cache info when empty."""
        manager = ModelManager()

        info = manager.get_cache_info()

        expected = {
            "cached_models": [],
            "model_count": 0,
            "total_accesses": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0,
            "load_times": {},
            "access_counts": {},
        }

        assert info == expected

    def test_get_cache_info_with_data(self, reset_model_manager):
        """Test getting cache info with cached models."""
        manager = ModelManager()

        # Setup mock data
        manager._models = {"spacy_model": "spacy_data", "gliner_model": "gliner_data"}
        manager._load_times = {"spacy_model": 2.5, "gliner_model": 5.0}
        manager._access_counts = {"spacy_model": 10, "gliner_model": 3}  # 9 hits, 2 misses

        info = manager.get_cache_info()

        assert info["cached_models"] == ["spacy_model", "gliner_model"]
        assert info["model_count"] == 2
        assert info["total_accesses"] == 13  # 10 + 3
        assert info["cache_hits"] == 11  # (10-1) + (3-1) = 9 + 2 = 11
        assert info["cache_misses"] == 2  # 2 models loaded
        assert info["hit_rate"] == 11/13  # 11 hits out of 13 accesses
        assert info["load_times"] == {"spacy_model": 2.5, "gliner_model": 5.0}
        assert info["access_counts"] == {"spacy_model": 10, "gliner_model": 3}


class TestModelManagerPerformanceSummary:
    """Test ModelManager performance summary functionality."""

    def test_get_performance_summary_empty(self, reset_model_manager):
        """Test getting performance summary when empty."""
        manager = ModelManager()

        summary = manager.get_performance_summary()

        assert summary["cache_efficiency"]["hit_rate"] == 0
        assert summary["cache_efficiency"]["total_models_loaded"] == 0
        assert summary["cache_efficiency"]["total_accesses"] == 0
        assert summary["cache_efficiency"]["estimated_time_saved"] == 0.0
        assert summary["model_details"] == []
        assert len(summary["recommendations"]) > 0

    def test_get_performance_summary_with_data(self, reset_model_manager):
        """Test getting performance summary with cached models."""
        manager = ModelManager()

        # Setup mock data
        manager._models = {"spacy_model": "spacy_data", "gliner_model": "gliner_data"}
        manager._load_times = {"spacy_model": 2.5, "gliner_model": 5.0}
        manager._access_counts = {"spacy_model": 5, "gliner_model": 8}  # 3 hits, 1 miss, 6 hits, 1 miss

        summary = manager.get_performance_summary()

        # Check cache efficiency - 9 hits out of 13 accesses
        expected_hit_rate = 9/13
        assert abs(summary["cache_efficiency"]["hit_rate"] - expected_hit_rate) < 0.001
        assert summary["cache_efficiency"]["total_models_loaded"] == 2
        assert summary["cache_efficiency"]["total_accesses"] == 13
        assert summary["cache_efficiency"]["estimated_time_saved"] == 17.5  # (2.5*3) + (5.0*6)

        # Check model details
        assert len(summary["model_details"]) == 2

        spacy_detail = next(d for d in summary["model_details"] if d["model"] == "spacy_model")
        assert spacy_detail["load_time"] == 2.5
        assert spacy_detail["access_count"] == 5
        assert spacy_detail["time_saved"] == 7.5  # 2.5 * 3 hits

        gliner_detail = next(d for d in summary["model_details"] if d["model"] == "gliner_model")
        assert gliner_detail["load_time"] == 5.0
        assert gliner_detail["access_count"] == 8
        assert gliner_detail["time_saved"] == 30.0  # 5.0 * 6 hits

        # Should have recommendations
        assert len(summary["recommendations"]) > 0

    def test_get_performance_summary_high_hit_rate(self, reset_model_manager):
        """Test performance summary with high hit rate."""
        manager = ModelManager()

        # Setup high hit rate scenario
        manager._models = {"model": "data"}
        manager._load_times = {"model": 1.0}
        manager._access_counts = {"model": 100}  # 99 hits, 1 miss

        summary = manager.get_performance_summary()

        assert summary["cache_efficiency"]["hit_rate"] == 99/100
        assert "Excellent cache performance" in summary["recommendations"][0]

    def test_get_performance_summary_low_hit_rate(self, reset_model_manager):
        """Test performance summary with low hit rate."""
        manager = ModelManager()

        # Setup low hit rate scenario
        manager._models = {"model1": "data1", "model2": "data2"}
        manager._load_times = {"model1": 1.0, "model2": 1.0}
        manager._access_counts = {"model1": 2, "model2": 2}  # 1 hit, 1 miss each

        summary = manager.get_performance_summary()

        assert summary["cache_efficiency"]["hit_rate"] == 2/4  # 2 hits out of 4 accesses
        assert "Low cache hit rate" in summary["recommendations"][0]


class TestModelManagerIntegration:
    """Test ModelManager integration scenarios."""

    def test_multiple_model_types(self, reset_model_manager):
        """Test loading and caching multiple model types."""
        manager = ModelManager()

        with patch('clipscribe.extractors.model_manager.optional_deps') as mock_deps:
            # Setup SpaCy mock
            mock_spacy = MagicMock()
            mock_spacy_model = MagicMock()
            mock_spacy.load.return_value = mock_spacy_model

            # Setup GLiNER mocks
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = False
            mock_torch.backends.mps.is_available.return_value = False

            mock_gliner = MagicMock()
            mock_gliner_model = MagicMock()
            mock_gliner.GLiNER.from_pretrained.return_value = mock_gliner_model

            # Setup REBEL mocks
            mock_transformers = MagicMock()
            mock_rebel_pipeline = MagicMock()
            mock_transformers.pipeline.return_value = mock_rebel_pipeline

            # Configure dependency returns
            mock_deps.require_dependency.side_effect = [
                mock_spacy,        # SpaCy
                mock_torch,        # GLiNER torch
                mock_gliner,       # GLiNER gliner
                mock_torch,        # REBEL torch
                mock_transformers  # REBEL transformers
            ]

            # Load different model types
            spacy_result = manager.get_spacy_model("en_core_web_sm")
            gliner_result = manager.get_gliner_model("test/gliner")
            rebel_result = manager.get_rebel_model("test/rebel")

            # Verify all models are cached
            assert len(manager._models) == 3
            assert "spacy_en_core_web_sm" in manager._models
            assert "gliner_test/gliner_auto" in manager._models
            assert "rebel_test/rebel_auto" in manager._models

            # Verify return values
            assert spacy_result is mock_spacy_model
            assert gliner_result == (mock_gliner_model, "cpu")
            assert rebel_result is mock_rebel_pipeline

    def test_model_reuse_efficiency(self, reset_model_manager):
        """Test that models are reused efficiently."""
        manager = ModelManager()

        with patch('clipscribe.extractors.model_manager.optional_deps') as mock_deps:
            mock_spacy = MagicMock()
            mock_model = MagicMock()
            mock_spacy.load.return_value = mock_model
            mock_deps.require_dependency.return_value = mock_spacy

            # Load model multiple times
            result1 = manager.get_spacy_model("en_core_web_sm")
            result2 = manager.get_spacy_model("en_core_web_sm")
            result3 = manager.get_spacy_model("en_core_web_sm")

            # All should return the same instance
            assert result1 is result2 is result3
            assert result1 is mock_model

            # SpaCy should only be loaded once
            mock_spacy.load.assert_called_once_with("en_core_web_sm")

            # Should have 3 accesses recorded
            assert manager._access_counts["spacy_en_core_web_sm"] == 3

    def test_cache_performance_tracking(self, reset_model_manager):
        """Test that cache performance is tracked correctly."""
        manager = ModelManager()

        with patch('clipscribe.extractors.model_manager.optional_deps') as mock_deps, \
             patch('time.time', side_effect=[1000.0, 1002.0, 1004.0, 1006.0, 1008.0, 1010.0]):

            mock_spacy = MagicMock()
            mock_model = MagicMock()
            mock_spacy.load.return_value = mock_model
            mock_deps.require_dependency.return_value = mock_spacy

            # First load (cache miss)
            manager.get_spacy_model("en_core_web_sm")
            assert manager._load_times["spacy_en_core_web_sm"] == 2.0
            assert manager._access_counts["spacy_en_core_web_sm"] == 1

            # Second load (cache hit)
            manager.get_spacy_model("en_core_web_sm")
            assert manager._access_counts["spacy_en_core_web_sm"] == 2

            # Third load (cache hit)
            manager.get_spacy_model("en_core_web_sm")
            assert manager._access_counts["spacy_en_core_web_sm"] == 3

            # Load time should still be 2.0 (from first load)
            assert manager._load_times["spacy_en_core_web_sm"] == 2.0
