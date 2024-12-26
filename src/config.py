# config.py

import os
from dotenv import load_dotenv
import re
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables from .env file
load_dotenv()

# Google Cloud settings
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Model versions
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")

# API keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Other settings
MAX_TOKENS = 2000000
TEMPERATURE = 0.2

# Output sections
OUTPUT_SECTIONS = [
    "executive_summary",
    "key_takeaways",
    "detailed_content_analysis",
    "main_topics",
    "key_themes",
    "key_figures",
    "key_locations",
    "quotes",
    "timeline",
    "review_questions",
    "sentiment_analysis",
    "entity_recognition",
    "transcript",
]

# Logging settings
LOG_DIR = "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.DEBUG
LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB
LOG_BACKUP_COUNT = 5

OUTPUT_FOLDER = "output"

# Clip generation settings
CLIP_MIN_DURATION = 15  # seconds
CLIP_MAX_DURATION = 60  # seconds
CLIP_TARGET_DURATION = 30  # seconds
CLIP_PADDING = 0.5  # seconds
SPEECH_DETECTION_THRESHOLD = 0.01  # for audio analysis

# Speech recognition settings
SPEECH_SAMPLE_RATE = 16000
SPEECH_MODEL = "latest_long"  # v2 model name
SPEECH_RECOGNIZER_PATH = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global/recognizers"
SPEECH_LANGUAGE_CODES = ["en-US"]  # v2 uses array of language codes

# Audio processing settings
WORDS_PER_SECOND = 2.5  # Average speaking rate
MIN_SEGMENT_CONFIDENCE = 0.8  # Minimum confidence for segments
AUDIO_FRAME_SIZE = 100  # Frame size in milliseconds

# Gemini settings
GEMINI_MAX_TOKENS = 2000000  # 2M token context window
GEMINI_TEMPERATURE = 0.1     # Higher for more creative responses
GEMINI_TOP_P = 0.8          # Nucleus sampling
GEMINI_TOP_K = 40           # Top-k sampling
GEMINI_STOP_SEQUENCES = ["```"]  # Stop at code blocks

def to_snake_case(text: str) -> str:
    """Convert text to snake case."""
    # Remove special characters and convert to lowercase
    text = ''.join(c.lower() if c.isalnum() or c.isspace() else '_' for c in text)
    # Replace spaces with underscores and remove consecutive underscores
    text = '_'.join(word for word in text.split('_') if word)
    return text

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with consistent configuration."""
    logger = logging.getLogger(name)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Set format to include full path for truncation prevention
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    
    # Create handlers with different levels
    file_handler = RotatingFileHandler(
        filename=os.path.join(LOG_DIR, f"{name}.log"),
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)  # Full debug info to file
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Only INFO and above to console
    
    # Set format
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger