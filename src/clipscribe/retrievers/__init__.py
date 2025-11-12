"""Video retrievers for ClipScribe."""

from .universal_video_client import UniversalVideoClient
from .youtube_client import YouTubeClient

__all__ = [
    "UniversalVideoClient",
    "YouTubeClient",
]
