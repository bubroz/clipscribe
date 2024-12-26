"""
ClipScribe: A YouTube video transcription and clip generation tool.

This module provides functionality for downloading YouTube videos,
transcribing their content, and generating clips based on user queries
or time ranges.
"""

from __future__ import annotations

import os
import sys
import json
import re
from typing import Tuple, Optional, Dict, Any, List, Union
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Third-party imports
import nltk
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip
from google.cloud import storage
import yt_dlp

# Local imports
from config import (
    GOOGLE_CLOUD_PROJECT,
    GEMINI_MODEL,
    OUTPUT_FOLDER,
    GEMINI_TEMPERATURE,
    GEMINI_TOP_P,
    GEMINI_TOP_K,
    GEMINI_MAX_TOKENS,
    to_snake_case,
    setup_logger
)
from transcription import process_audio
from post_processing_gemini import (
    GeminiPostProcessor,
    ClipSuggestion
)
from error_handling import (
    ClipScribeError,
    TranscriptionError,
    AudioProcessingError,
    YouTubeDownloadError,
    APIError,
    handle_error,
    raise_error,
)
from clip_utils import format_timestamp

# Constants
VALID_VIDEO_QUALITIES = ['360p', '480p', '720p', '1080p']
MAX_FILE_SIZE_MB = 480
MAX_DURATION_MINUTES = 480

# Initialize NLTK resources
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logger = setup_logger("clipscribe")

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# Define ProcessingResult type
ProcessingResult = Tuple[str, str, Dict[str, Any], Optional[str]]

class OutputPathManager:
    """Manages output paths and directory creation for ClipScribe."""
    
    @staticmethod
    def create_output_folder(name: str) -> str:
        """
        Create an output folder with a sanitized name.
        
        Args:
            name: The desired folder name
            
        Returns:
            The path to the created output folder
        """
        valid_name = re.sub(r'[^\w\s-]', '', name)
        valid_name = valid_name.replace(' ', '_')
        valid_name = valid_name[:255]
        
        output_dir = os.path.join('output', valid_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
        
    @staticmethod
    def get_save_paths(output_dir: str, video_title: str, file_path: str) -> Dict[str, str]:
        """
        Generate paths for saving various output files.
        
        Args:
            output_dir: Base output directory
            video_title: Title of the video
            file_path: Original file path
            
        Returns:
            Dictionary containing paths for different output files
        """
        return {
            "processed": os.path.join(output_dir, f"{to_snake_case(video_title)}_processed.json"),
            "raw": os.path.join(output_dir, f"raw_api_response_{os.path.basename(file_path)}.json"),
            "transcript": os.path.join(output_dir, f"{to_snake_case(video_title)}_transcript.txt"),
            "metadata": os.path.join(output_dir, f"{to_snake_case(video_title)}_metadata.json")
        }

class CredentialsChecker:
    """Handles verification of required credentials and environment variables."""
    
    @staticmethod
    def check_google_credentials() -> None:
        """
        Verify that all required Google Cloud credentials are present.
        
        Raises:
            EnvironmentError: If required credentials are missing
        """
        try:
            if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                raise EnvironmentError(
                    "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set."
                )
            
            logger.info(f"GOOGLE_CLOUD_PROJECT is set to: {GOOGLE_CLOUD_PROJECT}")
            credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            logger.info(f"Google Cloud credentials found at: {credentials_path}")
            
            required_vars = ["GEMINI_API_KEY"]
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            if missing_vars:
                raise_error(
                    ValueError,
                    f"Missing required environment variables: {', '.join(missing_vars)}"
                )

        except Exception as e:
            logger.error(f"Error checking Google credentials: {str(e)}")
            raise

class YouTubeUtils:
    """Utility functions for handling YouTube URLs and metadata."""
    
    @staticmethod
    def clean_youtube_url(url: str) -> str:
        """
        Clean a YouTube URL to its basic form.
        
        Args:
            url: The YouTube URL to clean
            
        Returns:
            The cleaned YouTube URL
        """
        parsed_url = urlparse(url)
        
        if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
            if 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path.lstrip('/')
            else:
                query_params = parse_qs(parsed_url.query)
                video_id = query_params.get('v', [None])[0]
            
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
        
        return url
        
    @staticmethod
    def format_youtube_metadata(metadata: Dict[str, Any]) -> str:
        """
        Format YouTube metadata into a readable string.
        
        Args:
            metadata: Dictionary containing YouTube metadata
            
        Returns:
            Formatted metadata string
        """
        return f"""
        YouTube Video Metadata:
        Title: {metadata.get('title', 'N/A')}
        Author: {metadata.get('author', 'N/A')}
        URL: {metadata.get('url', 'N/A')}
        Publish Date: {metadata.get('publish_date', 'N/A')}
        Views: {metadata.get('views', 'N/A')}
        Duration: {metadata.get('duration', 'N/A')} seconds
        Description: {metadata.get('description', 'N/A')}
        """
class MediaInfoHandler:
    """Handles media file information and validation."""
    
    def validate_media_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate and get information about a media file.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Dict containing media information
            
        Raises:
            AudioProcessingError: If validation fails
        """
        try:
            # Use moviepy instead of AudioSegment
            video = VideoFileClip(file_path)
            duration = video.duration  # in seconds
            
            info = {
                'duration': duration,
                'size': os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            }
            
            video.close()
            return info
            
        except Exception as e:
            raise AudioProcessingError(f"Failed to validate media file: {str(e)}")
    
    @staticmethod
    def get_media_files(directory: str) -> List[str]:
        """
        Get a list of media files in the specified directory.
        
        Args:
            directory: The directory to search for media files
            
        Returns:
            List of media file names found in the directory
        """
        media_extensions = [".mp3", ".wav", ".m4a", ".mp4", ".webm", ".mpeg", ".mpga"]
        return [
            f
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
            and os.path.splitext(f)[1].lower() in media_extensions
        ]

class FileProcessor:
    """Handles saving and loading of various file types."""
    
    @staticmethod
    def save_transcript(transcript: Dict[str, Any], output_path: str) -> str:
        """
        Save the transcript as JSON.
        
        Args:
            transcript: The transcript content to save
            output_path: The full path to save the transcript
            
        Returns:
            The path to the saved transcript file
            
        Raises:
            IOError: If there's an error saving the transcript
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, indent=2)
            logger.info(f"Transcript saved to: {output_path}")
            return output_path
        except IOError as e:
            logger.error(f"Error saving transcript to {output_path}: {str(e)}")
            raise

    @staticmethod
    def save_all_outputs(
        save_paths: Dict[str, str],
        transcript: Dict[str, Any],
        final_output: Dict[str, Any],
        raw_api_response: Dict[str, Any],
        youtube_metadata: Dict[str, Any],
        model: str
    ) -> None:
        """
        Save all output files including transcript, metadata, and processed results.
        
        Args:
            save_paths: Dictionary of paths for different output files
            transcript: The transcript data
            final_output: The processed output data
            raw_api_response: Raw API response data
            youtube_metadata: YouTube video metadata
            model: The model used for processing
        """
        try:
            for key, path in save_paths.items():
                with open(path, 'w', encoding='utf-8') as f:
                    if key == "transcript":
                        f.write(transcript["transcript"])
                    elif key == "metadata":
                        json.dump({
                            "youtube_metadata": youtube_metadata,
                            "transcript_metadata": transcript.get("metadata", {}),
                            "processing_metadata": {
                                "model": model,
                                "timestamp": datetime.now().isoformat(),
                                "duration": transcript.get("totalBilledDuration", "unknown")
                            }
                        }, f, indent=2)
                    else:
                        json.dump(
                            final_output if key == "processed" else raw_api_response,
                            f,
                            indent=2
                        )
        except IOError as e:
            logger.error(f"Error saving outputs: {str(e)}")
            raise

class AudioProcessor:
    """Main class for processing audio files and YouTube videos."""
    
    def __init__(self, post_processor: GeminiPostProcessor):
        """Initialize audio processor."""
        self.file_processor = FileProcessor()
        self.post_processor = post_processor
        
    def _create_output_folder(self, video_title: str) -> str:
        """Create standardized output folder name."""
        # Convert to snake case and ensure consistent casing
        folder_name = to_snake_case(video_title)
        output_dir = os.path.join('output', folder_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def process_audio_file(
        self,
        url: str,
        base_name: str,
        is_youtube_url: bool = True,
        keep_video: bool = False,
        video_quality: str = '720p'
    ) -> Dict[str, Any]:
        """Process audio file and return results."""
        try:
            # Process audio and get results dictionary
            result = process_audio(
                url,
                is_youtube_url=is_youtube_url,
                keep_video=keep_video,
                video_quality=video_quality,
                post_processor=self.post_processor
            )
            
            # Just return the result, don't try to display it
            return result

        except Exception as e:
            logger.error(f"Error in process_audio_file: {str(e)}")
            raise

class ClipGenerator:
    """Handles the generation of video clips based on user queries or time ranges."""
    
    def __init__(self, processor: GeminiPostProcessor) -> None:
        """
        Initialize the ClipGenerator.
        
        Args:
            processor: Instance of GeminiPostProcessor for content analysis
        """
        self.processor = processor
        
    def process_clip_by_query(
        self,
        video_path: str,
        transcript_path: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Generate clips based on a search query.
        
        Args:
            video_path: Path to the video file
            transcript_path: Path to the transcript file
            query: Search query for finding relevant segments
            
        Returns:
            List of clip suggestions with metadata
        """
        try:
            with open(transcript_path, 'r') as f:
                transcript_data = json.load(f)
                
            clips = self.processor.find_and_create_clips(
                video_path=video_path,
                search_concept=query,
                transcript_data=transcript_data
            )
            
            return clips
        except Exception as e:
            logger.error(f"Error processing clip by query: {str(e)}")
            raise

    def create_clip_from_timerange(
        self,
        video_path: str,
        start_time: str,
        end_time: str,
        output_dir: str
    ) -> str:
        """
        Create a clip from specified time range.
        
        Args:
            video_path: Path to the video file
            start_time: Start time in MM:SS format
            end_time: End time in MM:SS format
            output_dir: Directory to save the clip
            
        Returns:
            Path to the created clip
            
        Raises:
            ValueError: If time format is invalid
        """
        try:
            start_m, start_s = map(int, start_time.split(":"))
            end_m, end_s = map(int, end_time.split(":"))
            
            clip = VideoFileClip(video_path).subclip(
                start_m * 60 + start_s,
                end_m * 60 + end_s
            )
            
            output_path = os.path.join(
                output_dir,
                f"custom_clip_{start_time.replace(':', '_')}-{end_time.replace(':', '_')}.mp4"
            )
            
            clip.write_videofile(output_path)
            clip.close()
            
            return output_path
        except ValueError as e:
            logger.error(f"Invalid time format: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating clip: {str(e)}")
            raise

class ClipScribeCLI:
    """Command Line Interface for ClipScribe."""
    
    def __init__(self) -> None:
        """Initialize the CLI interface."""
        # Create single instance of GeminiPostProcessor
        self.post_processor = GeminiPostProcessor()
        # Pass the instance to AudioProcessor
        self.audio_processor = AudioProcessor(post_processor=self.post_processor)
        
    def process_youtube_video(self, test_url: str = None) -> None:
        """Handle YouTube video processing workflow."""
        try:
            CredentialsChecker.check_google_credentials()

            if test_url:
                youtube_url = test_url
                print(f"Processing test URL: {youtube_url}")
            else:
                youtube_url = input("Enter the YouTube URL: ").strip()
            
            clean_url = YouTubeUtils.clean_youtube_url(youtube_url)
            logger.info(f"Processing YouTube URL: {clean_url}")
            
            keep_video = input(
                "Do you want to keep the downloaded video? (y/n): "
            ).strip().lower() == 'y'
            
            video_quality = '720p'
            if keep_video:
                while video_quality not in VALID_VIDEO_QUALITIES:
                    video_quality = input(
                        f"Select video quality {VALID_VIDEO_QUALITIES}: "
                    ).strip().lower()
                    if video_quality not in VALID_VIDEO_QUALITIES:
                        print("Invalid quality option. Please try again.")

            # Get video info first to use title as base name
            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.extract_info(clean_url, download=False)
                video_title = info.get('title', '')
                base_name = to_snake_case(video_title)  # Use video title instead of URL

            result = self.audio_processor.process_audio_file(
                clean_url,
                base_name,  # Pass sanitized video title as base_name
                is_youtube_url=True,
                keep_video=keep_video,
                video_quality=video_quality
            )
            
            # Display results here instead
            self.display_processing_results(result)
            
        except Exception as e:
            handle_error(e)

    def process_clips(self) -> None:
        """Handle clip generation workflow."""
        try:
            output_dirs = [
                d for d in os.listdir(OUTPUT_FOLDER)
                if os.path.isdir(os.path.join(OUTPUT_FOLDER, d))
            ]
            
            if not output_dirs:
                print("\nNo processed videos found. Process a video first.")
                return
                
            self._display_processed_videos(output_dirs)
            video_idx = int(input("\nSelect video number: ")) - 1
            video_dir = output_dirs[video_idx]
            
            files = os.listdir(os.path.join(OUTPUT_FOLDER, video_dir))
            raw_response_file = next(
                (f for f in files if f.startswith('raw_api_response_') and f.endswith('.json')),
                None
            )
            video_file = next(
                (f for f in files if f.endswith('.mp4')),
                None
            )

            if not raw_response_file or not video_file:
                print("\nError: Required files not found. Please process the video first.")
                return

            video_path = os.path.join(OUTPUT_FOLDER, video_dir, video_file)
            transcript_path = os.path.join(OUTPUT_FOLDER, video_dir, raw_response_file)
            
            self._handle_clip_options(video_path, transcript_path, video_dir)
            
        except Exception as e:
            handle_error(e)

    def display_processing_results(self, result: Dict[str, Any]) -> None:
        """Display the results of video processing."""
        print("\nProcessing completed successfully")
        print(f"Files saved to:")
        for key, path in result["paths"].items():
            if path:  # Only print if path exists
                print(f"- {key.title()}: {path}")

        if result.get("metadata"):
            print("\nYouTube Video Metadata:")
            for key in ['title', 'author', 'url', 'publish_date', 'views', 'duration']:
                if key in result["metadata"]:
                    print(f"{key.title()}: {result['metadata'][key]}")

    def _display_processed_videos(self, output_dirs: List[str]) -> None:
        """Display list of processed videos."""
        print("\nProcessed Videos:")
        for i, dirname in enumerate(output_dirs, 1):
            print(f"{i}. {dirname.replace('_', ' ').title()}")

    def _handle_clip_options(
        self,
        video_path: str,
        transcript_path: str,
        video_dir: str
    ) -> None:
        """Handle clip generation options workflow."""
        print("\nClip Options:")
        print("1. Search by topic/concept")
        print("2. Custom time range")
        
        clip_choice = input("\nEnter choice (1-2): ")
        
        if clip_choice == "1":
            self._handle_concept_search(video_path, transcript_path)
        elif clip_choice == "2":
            self._handle_timerange_clip(video_path, video_dir)

    def _handle_concept_search(self, video_path: str, transcript_path: str) -> None:
        """Handle concept-based clip generation."""
        try:
            # Get the output directory
            output_dir = os.path.dirname(video_path)
            
            # Load processed.json
            processed_path = os.path.join(output_dir, "processed.json")
            if not os.path.exists(processed_path):
                print("\nError: processed.json not found. Please process the video first.")
                return
            
            with open(processed_path, 'r') as f:
                processed_data = json.load(f)
            
            # First, get video analysis
            print("\nAnalyzing video content...")
            
            # Create analysis file if it doesn't exist
            analysis_path = os.path.join(output_dir, f"{os.path.basename(output_dir)}_analysis.json")
            if not os.path.exists(analysis_path):
                segments = self.post_processor.create_logical_segments(processed_data)
                if not segments:
                    print("\nError: Could not analyze video content.")
                    return
                
            # Load and display analysis
            with open(analysis_path, 'r') as f:
                analysis_data = json.load(f)
            
            print("\n=== Video Summary ===")
            print(analysis_data.get("summary", "No summary available"))
            print("\n===================")
            
            print("\nNow you can ask specific questions about the content!")
            print("Examples:")
            print("- Find parts where they talk about X")
            print("- Show me segments about Y")
            print("- Find the section discussing Z")
            print("(Type 'exit' to return to main menu)")

            while True:
                query = input("\nWhat would you like to find? ")
                if query.lower() == 'exit':
                    break

                suggestions = self.post_processor.search_transcript_segments(
                    query,
                    processed_data
                )
                
                if not suggestions:
                    print("\nNo relevant segments found. Try rephrasing your query.")
                    continue
                    
                print(f"\nFound {len(suggestions)} relevant segments:")
                for i, s in enumerate(suggestions, 1):
                    print(f"\n{i}. {s.topic.upper()}")
                    print(f"   Text: \"{s.text}\"")
                    print(f"   Time: {format_timestamp(s.start_time)} - {format_timestamp(s.end_time)}")
                    print(f"   Duration: {s.end_time - s.start_time:.1f}s")
                    print(f"   Explanation: {s.explanation}")
                    print(f"   Relevance: {'★' * int(s.confidence * 5)}")
                    
                    if input("\nCreate clip of this segment? (y/n): ").lower() == 'y':
                        try:
                            clip_path = self.post_processor.create_clip(video_path, s)
                            print(f"   ✓ Clip saved to: {clip_path}")
                        except Exception as e:
                            print(f"   ✗ Failed to create clip: {str(e)}")

        except Exception as e:
            logger.error(f"Error in concept search: {str(e)}", exc_info=True)
            print("\nError processing your query. Please try again.")

    def _handle_timerange_clip(self, video_path: str, video_dir: str) -> None:
        """Handle time-range based clip generation."""
        start = input("\nEnter start time (MM:SS): ")
        end = input("Enter end time (MM:SS): ")
        
        try:
            # Convert MM:SS to seconds
            start_parts = start.split(":")
            end_parts = end.split(":")
            start_seconds = int(start_parts[0]) * 60 + int(start_parts[1])
            end_seconds = int(end_parts[0]) * 60 + int(end_parts[1])
            
            # Create clip suggestion
            suggestion = ClipSuggestion(
                text="Custom time range clip",
                start_time=float(start_seconds),
                end_time=float(end_seconds),
                confidence=1.0,
                explanation="User-specified time range",
                topic="custom_clip"
            )
            
            # Use post_processor to create clip
            output_path = self.post_processor.create_clip(video_path, suggestion)
            print(f"\nClip saved to: {output_path}")
        except ValueError:
            print("\nInvalid time format. Please use MM:SS format.")
        except Exception as e:
            print(f"\nError creating clip: {str(e)}")

def main() -> None:
    """Main entry point for the ClipScribe application."""
    print("Welcome to ClipScribe!")
    cli = ClipScribeCLI()

    # Add test URL constant
    TEST_URL = "https://www.youtube.com/watch?v=eIho2S0ZahI&t=23s"

    while True:
        print("\nClipScribe Menu:")
        print("1. Process new YouTube video")
        print("2. Process test YouTube video")
        print("3. Create clips from processed video")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            cli.process_youtube_video()
        elif choice == "2":
            cli.process_youtube_video(test_url=TEST_URL)
        elif choice == "3":
            cli.process_clips()
        elif choice == "4":
            break

if __name__ == "__main__":
    main()