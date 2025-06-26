"""
Model Manager for ClipScribe - Singleton pattern for ML model instances.

This module ensures that expensive ML models (GLiNER, REBEL, SpaCy) are loaded
only once and reused across multiple video processing operations. Now includes
performance monitoring for cache hits and load times.
"""

import logging
from typing import Optional, Dict, Any
import warnings
import os
import time

# Suppress the tokenizer warning that appears every time
warnings.filterwarnings("ignore", message=".*sentencepiece tokenizer.*")
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Prevent tokenizer warnings

logger = logging.getLogger(__name__)


class ModelManager:
    """Singleton manager for ML models to prevent repeated loading."""
    
    _instance = None
    _models: Dict[str, Any] = {}
    _performance_monitor = None
    _load_times: Dict[str, float] = {}
    _access_counts: Dict[str, int] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        logger.info("Initializing ModelManager singleton with performance monitoring")
    
    def set_performance_monitor(self, monitor):
        """Set the performance monitor for tracking cache performance."""
        self._performance_monitor = monitor
        logger.debug("Performance monitor attached to ModelManager")
    
    def _record_cache_hit(self, model_key: str):
        """Record a cache hit for performance monitoring."""
        self._access_counts[model_key] = self._access_counts.get(model_key, 0) + 1
        
        if self._performance_monitor:
            # Use previous load time if available
            load_time = self._load_times.get(model_key)
            self._performance_monitor.record_model_cache_hit(model_key, load_time)
        
        logger.debug(f"Cache hit for {model_key} (access #{self._access_counts[model_key]})")
    
    def _record_cache_miss(self, model_key: str, load_time: float):
        """Record a cache miss (new model load) for performance monitoring."""
        self._load_times[model_key] = load_time
        self._access_counts[model_key] = 1
        
        if self._performance_monitor:
            self._performance_monitor.record_model_cache_miss(model_key, load_time)
        
        logger.info(f"Cache miss for {model_key} - loaded in {load_time:.2f}s")
    
    def get_spacy_model(self, model_name: str = "en_core_web_sm"):
        """Get or load SpaCy model with performance tracking."""
        key = f"spacy_{model_name}"
        
        if key not in self._models:
            logger.info(f"Loading SpaCy model {model_name} (one-time load)...")
            start_time = time.time()
            
            import spacy
            self._models[key] = spacy.load(model_name)
            
            load_time = time.time() - start_time
            self._record_cache_miss(key, load_time)
            logger.info(f"SpaCy model {model_name} loaded successfully in {load_time:.2f}s :-)")
        else:
            self._record_cache_hit(key)
        
        return self._models[key]
    
    def get_gliner_model(self, model_name: str = "urchade/gliner_multi-v2.1", device: str = "auto"):
        """Get or load GLiNER model with performance tracking."""
        key = f"gliner_{model_name}_{device}"
        
        if key not in self._models:
            logger.info(f"Loading GLiNER model {model_name} on {device} (one-time load)...")
            start_time = time.time()
            
            try:
                import torch
                from gliner import GLiNER
                
                # Determine device
                if device == "auto":
                    if torch.cuda.is_available():
                        device = "cuda"
                    elif torch.backends.mps.is_available():
                        device = "mps"
                    else:
                        device = "cpu"
                
                # Suppress warnings during model loading
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model = GLiNER.from_pretrained(model_name)
                    if device != "cpu":
                        model = model.to(device)
                
                self._models[key] = (model, device)
                
                load_time = time.time() - start_time
                self._record_cache_miss(key, load_time)
                logger.info(f"GLiNER model loaded and cached successfully in {load_time:.2f}s :-)")
                
            except Exception as e:
                logger.error(f"Failed to load GLiNER model: {e}")
                raise
        else:
            self._record_cache_hit(key)
        
        return self._models[key]
    
    def get_rebel_model(self, model_name: str = "Babelscape/rebel-large", device: str = "auto"):
        """Get or load REBEL model with performance tracking."""
        key = f"rebel_{model_name}_{device}"
        
        if key not in self._models:
            logger.info(f"Loading REBEL model {model_name} on {device} (one-time load)...")
            start_time = time.time()
            
            try:
                import torch
                from transformers import pipeline
                
                # Determine device
                if device == "auto":
                    if torch.cuda.is_available():
                        device = 0  # CUDA device index
                    elif torch.backends.mps.is_available():
                        device = "mps"
                    else:
                        device = -1  # CPU
                else:
                    # Convert device string to pipeline format
                    if device == "cuda":
                        device = 0
                    elif device == "cpu":
                        device = -1
                
                # Suppress warnings during model loading
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    triplet_extractor = pipeline(
                        'text2text-generation',
                        model=model_name,
                        tokenizer=model_name,
                        device=device,
                        max_length=256
                    )
                
                self._models[key] = triplet_extractor
                
                load_time = time.time() - start_time
                self._record_cache_miss(key, load_time)
                logger.info(f"REBEL model loaded and cached successfully in {load_time:.2f}s :-)")
                
            except Exception as e:
                logger.error(f"Failed to load REBEL model: {e}")
                raise
        else:
            self._record_cache_hit(key)
        
        return self._models[key]
    
    def clear_cache(self):
        """Clear all cached models (useful for memory management)."""
        logger.info(f"Clearing {len(self._models)} cached models")
        self._models.clear()
        self._load_times.clear()
        self._access_counts.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached models and performance stats."""
        total_accesses = sum(self._access_counts.values())
        cache_hits = sum(count - 1 for count in self._access_counts.values() if count > 1)
        cache_misses = len(self._access_counts)  # Each model loaded once
        
        return {
            "cached_models": list(self._models.keys()),
            "model_count": len(self._models),
            "total_accesses": total_accesses,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_rate": cache_hits / total_accesses if total_accesses > 0 else 0,
            "load_times": dict(self._load_times),
            "access_counts": dict(self._access_counts)
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a detailed performance summary."""
        cache_info = self.get_cache_info()
        
        summary = {
            "cache_efficiency": {
                "hit_rate": cache_info["hit_rate"],
                "total_models_loaded": cache_info["model_count"],
                "total_accesses": cache_info["total_accesses"],
                "estimated_time_saved": 0.0
            },
            "model_details": [],
            "recommendations": []
        }
        
        # Calculate time savings
        total_load_time = sum(self._load_times.values())
        potential_load_time = sum(
            self._load_times.get(model, 0) * (self._access_counts.get(model, 1) - 1)
            for model in self._models.keys()
        )
        summary["cache_efficiency"]["estimated_time_saved"] = potential_load_time
        
        # Per-model details
        for model_key in self._models.keys():
            load_time = self._load_times.get(model_key, 0)
            access_count = self._access_counts.get(model_key, 1)
            
            summary["model_details"].append({
                "model": model_key,
                "load_time": load_time,
                "access_count": access_count,
                "time_saved": load_time * (access_count - 1)
            })
        
        # Generate recommendations
        if cache_info["hit_rate"] > 0.8:
            summary["recommendations"].append(
                f"Excellent cache performance! {cache_info['hit_rate']:.1%} hit rate is providing significant speedup"
            )
        elif cache_info["hit_rate"] > 0.5:
            summary["recommendations"].append(
                f"Good cache performance at {cache_info['hit_rate']:.1%} hit rate"
            )
        else:
            summary["recommendations"].append(
                "Low cache hit rate - models may be getting cleared too frequently"
            )
        
        if potential_load_time > 10:
            summary["recommendations"].append(
                f"Model caching saved approximately {potential_load_time:.1f} seconds of load time"
            )
        
        return summary


# Global instance
model_manager = ModelManager() 