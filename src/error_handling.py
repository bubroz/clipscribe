import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class ClipScribeError(Exception):
    """Base exception class for ClipScribe errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class TranscriptionError(ClipScribeError):
    """Exception raised for errors during the transcription process."""
    pass

class PostProcessingError(ClipScribeError):
    """Exception raised for errors during the post-processing stage."""
    pass

class AudioProcessingError(ClipScribeError):
    """Exception raised for errors during audio file processing."""
    pass

class YouTubeDownloadError(ClipScribeError):
    """Exception raised for errors during YouTube video download."""
    pass

class APIError(ClipScribeError):
    """Exception raised for errors related to API calls."""
    pass

def log_error(error: ClipScribeError, log_level: int = logging.ERROR):
    """
    Log an error with standardized formatting.

    Args:
        error (ClipScribeError): The error to log.
        log_level (int): The logging level to use (default: logging.ERROR).
    """
    logger.log(log_level, f"{error.__class__.__name__}: {error.message}", exc_info=True, extra=error.details)

def handle_error(error: ClipScribeError):
    """
    Handle an error by logging it and performing any necessary cleanup or recovery actions.

    Args:
        error (ClipScribeError): The error to handle.
    """
    log_error(error)

    if isinstance(error, TranscriptionError):
        # Perform any necessary cleanup or recovery actions for transcription errors
        pass
    elif isinstance(error, PostProcessingError):
        # Perform any necessary cleanup or recovery actions for post-processing errors
        pass
    elif isinstance(error, AudioProcessingError):
        # Perform any necessary cleanup or recovery actions for audio processing errors
        pass
    elif isinstance(error, YouTubeDownloadError):
        # Provide instructions for manual download
        print("Error: Unable to automatically download the YouTube audio.")
        print("Please follow these steps to manually download the audio:")
        print("1. Visit https://youtube4kdownloader.com/ or a similar YouTube to MP3 converter.")
        print("2. Paste the YouTube URL and download the audio as an MP3 file.")
        print("3. Place the downloaded MP3 file in the 'resources' folder of this project.")
        print("4. Run the script again and choose the 'file' option to process the downloaded audio.")
    elif isinstance(error, APIError):
        # Perform any necessary cleanup or recovery actions for API errors
        pass
    else:
        # Handle any other types of errors
        print(f"An unexpected error occurred: {error.message}")
        print("Please check the log file for more details.")

def raise_error(error_class: type, message: str, details: Optional[Dict[str, Any]] = None):
    """
    Raise a ClipScribe error with the given error class, message, and optional details.

    Args:
        error_class (type): The ClipScribeError subclass to raise.
        message (str): The error message.
        details (Optional[Dict[str, Any]]): Additional details about the error.

    Raises:
        ClipScribeError: The specified error class with the given message and details.
    """
    raise error_class(message, details)