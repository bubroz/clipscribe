"""
Model Manager for ClipScribe - Singleton pattern for ML model instances.

This module ensures that expensive ML models (GLiNER, REBEL, SpaCy) are loaded
only once and reused across multiple video processing operations.
"""

import logging
from typing import Optional, Dict, Any
import warnings
import os

# Suppress the tokenizer warning that appears every time
warnings.filterwarnings("ignore", message=".*sentencepiece tokenizer.*")
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Prevent tokenizer warnings

logger = logging.getLogger(__name__)


class ModelManager:
    """Singleton manager for ML models to prevent repeated loading."""
    
    _instance = None
    _models: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        logger.info("Initializing ModelManager singleton")
    
    def get_spacy_model(self, model_name: str = "en_core_web_sm"):
        """Get or load SpaCy model."""
        key = f"spacy_{model_name}"
        if key not in self._models:
            logger.info(f"Loading SpaCy model {model_name} (one-time load)...")
            import spacy
            self._models[key] = spacy.load(model_name)
        return self._models[key]
    
    def get_gliner_model(self, model_name: str = "urchade/gliner_multi-v2.1", device: str = "auto"):
        """Get or load GLiNER model."""
        key = f"gliner_{model_name}_{device}"
        if key not in self._models:
            logger.info(f"Loading GLiNER model {model_name} on {device} (one-time load)...")
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
                logger.info("GLiNER model loaded and cached successfully :-)")
            except Exception as e:
                logger.error(f"Failed to load GLiNER model: {e}")
                raise
        
        return self._models[key]
    
    def get_rebel_model(self, model_name: str = "Babelscape/rebel-large", device: str = "auto"):
        """Get or load REBEL model."""
        key = f"rebel_{model_name}_{device}"
        if key not in self._models:
            logger.info(f"Loading REBEL model {model_name} on {device} (one-time load)...")
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
                logger.info("REBEL model loaded and cached successfully :-)")
            except Exception as e:
                logger.error(f"Failed to load REBEL model: {e}")
                raise
        
        return self._models[key]
    
    def clear_cache(self):
        """Clear all cached models (useful for memory management)."""
        logger.info(f"Clearing {len(self._models)} cached models")
        self._models.clear()
    
    def get_cache_info(self) -> Dict[str, str]:
        """Get information about cached models."""
        return {
            "cached_models": list(self._models.keys()),
            "model_count": len(self._models)
        }


# Global instance
model_manager = ModelManager() 