"""Provider factory for selecting transcription and intelligence providers."""

from typing import Literal
from .base import TranscriptionProvider, IntelligenceProvider, ConfigurationError

TranscriptionProviderType = Literal["voxtral", "whisperx-modal", "whisperx-local"]
IntelligenceProviderType = Literal["grok"]


def get_transcription_provider(
    provider_name: TranscriptionProviderType,
    **kwargs
) -> TranscriptionProvider:
    """Get transcription provider by name.
    
    Args:
        provider_name: Provider to use (voxtral, whisperx-modal, whisperx-local)
        **kwargs: Provider-specific configuration
        
    Returns:
        Initialized TranscriptionProvider instance
        
    Raises:
        ValueError: If provider_name is invalid
        ConfigurationError: If provider configuration is invalid
        
    Examples:
        >>> transcriber = get_transcription_provider("voxtral")
        >>> result = await transcriber.transcribe("audio.mp3")
    """
    # Import providers (lazy loading)
    from .transcription.voxtral import VoxtralProvider
    from .transcription.whisperx_modal import WhisperXModalProvider
    from .transcription.whisperx_local import WhisperXLocalProvider
    
    providers = {
        "voxtral": VoxtralProvider,
        "whisperx-modal": WhisperXModalProvider,
        "whisperx-local": WhisperXLocalProvider,
    }
    
    provider_cls = providers.get(provider_name)
    if not provider_cls:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown transcription provider: {provider_name}\n"
            f"Available providers: {available}"
        )
    
    # Initialize provider
    try:
        provider = provider_cls(**kwargs)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to initialize {provider_name} provider: {e}"
        )
    
    # Validate configuration
    if not provider.validate_config():
        raise ConfigurationError(
            f"Provider {provider_name} configuration invalid.\n"
            f"Check API keys and dependencies.\n"
            f"Run: clipscribe utils check-auth"
        )
    
    return provider


def get_intelligence_provider(
    provider_name: IntelligenceProviderType,
    **kwargs
) -> IntelligenceProvider:
    """Get intelligence provider by name.
    
    Args:
        provider_name: Provider to use (currently only 'grok')
        **kwargs: Provider-specific configuration
        
    Returns:
        Initialized IntelligenceProvider instance
        
    Raises:
        ValueError: If provider_name is invalid
        ConfigurationError: If provider configuration is invalid
        
    Examples:
        >>> extractor = get_intelligence_provider("grok")
        >>> intelligence = await extractor.extract(transcript)
    """
    # Import providers (lazy loading)
    from .intelligence.grok import GrokProvider
    
    providers = {
        "grok": GrokProvider,
    }
    
    provider_cls = providers.get(provider_name)
    if not provider_cls:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown intelligence provider: {provider_name}\n"
            f"Available providers: {available}\n"
            f"Note: Claude and GPT support can be added easily in future."
        )
    
    # Initialize provider
    try:
        provider = provider_cls(**kwargs)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to initialize {provider_name} provider: {e}"
        )
    
    # Validate configuration
    if not provider.validate_config():
        raise ConfigurationError(
            f"Provider {provider_name} configuration invalid.\n"
            f"Check API keys (XAI_API_KEY for Grok).\n"
            f"Run: clipscribe utils check-auth"
        )
    
    return provider

