"""
Transcription Module: Handles audio processing and speech-to-text conversion.

This module provides functionality for:
- Downloading and processing YouTube videos
- Converting audio to text using Google Cloud Speech-to-Text
- Managing GCS storage operations
- Processing and formatting transcription results
"""

from __future__ import annotations

import os
import time
import json
import glob
from typing import Any, Dict, List, Optional, Tuple, Union
import re

# Google Cloud imports
from google.cloud import storage
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2 import types as cloud_speech
from google.api_core import retry
from google.api_core import exceptions as google_exceptions
from google.protobuf.json_format import MessageToDict

# Third-party imports
import yt_dlp

# Local imports
from config import (
    GOOGLE_CLOUD_PROJECT,
    OUTPUT_FOLDER,
    to_snake_case,
    SPEECH_LANGUAGE_CODES,
    setup_logger
)
try:
    from error_handling import TranscriptionError, AudioProcessingError, YouTubeDownloadError
except ImportError:
    from src.error_handling import TranscriptionError, AudioProcessingError, YouTubeDownloadError

# At the top with other imports
from post_processing_gemini import GeminiPostProcessor

# Type aliases
PathStr = str
JsonDict = Dict[str, Any]
FileMetadata = Tuple[str, float, Dict[str, Any], Optional[str], float]
TranscriptionResult = Tuple[Dict[str, Any], float, str, Dict[str, Any], Optional[str]]

# Constants
MAX_TRANSCRIPTION_WAIT = 3600  # 1 hour
SUPPORTED_AUDIO_EXTENSIONS = ['.m4a', '.mp4', '.wav']

# Configure logging using centralized configuration
logger = setup_logger("transcription")

# Import Retry at the top
from google.api_core.retry import Retry, if_exception_type

# Define your retry configuration
retry_config = Retry(
    initial=1.0,
    maximum=60.0,
    multiplier=2.0,
    deadline=600.0,
    predicate=retry.if_exception_type(
        google_exceptions.DeadlineExceeded,
        google_exceptions.ServiceUnavailable,
        google_exceptions.ResourceExhausted,
        google_exceptions.InternalServerError,
    ),
)

class GCSManager:
    """Handles Google Cloud Storage operations."""
    
    def __init__(self, project_id: str):
        """
        Initialize GCS manager.
        
        Args:
            project_id: Google Cloud project ID
        """
        self.project_id = project_id
        self.storage_client = storage.Client(project=project_id)
        self.bucket_name = f"{project_id}-audio-files"
    
    def upload_file(self, file_path: str, chunk_size: int = None, retry_config: Any = None) -> str:
        """
        Upload a file to Google Cloud Storage.
        
        Args:
            file_path: Path to the file to upload
            chunk_size: Size of upload chunks in bytes
            retry_config: Retry configuration for uploads
            
        Returns:
            GCS URI of the uploaded file
            
        Raises:
            Exception: If upload fails
        """
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob_name = os.path.basename(file_path)
            blob = bucket.blob(blob_name)
            
            # Configure chunked upload if specified
            if chunk_size:
                blob.chunk_size = chunk_size
            
            # Upload with retry if configured
            if retry_config:
                blob.upload_from_filename(
                    file_path,
                    retry=retry_config,
                    timeout=120  # 2 minute timeout per attempt
                )
            else:
                blob.upload_from_filename(file_path)
            
            gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
            logger.info(f"File {file_path} uploaded to {gcs_uri}")
            return gcs_uri
        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to GCS. Error: {str(e)}")
            raise
    
    def delete_file(self, gcs_uri: str) -> None:
        """
        Delete a file from Google Cloud Storage.
        
        Args:
            gcs_uri: GCS URI of the file to delete
        """
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(os.path.basename(gcs_uri))
            blob.delete()
            logger.info(f"Deleted file from GCS: {gcs_uri}")
        except Exception as e:
            logger.warning(f"Error deleting file from GCS: {str(e)}")

class YouTubeDownloader:
    """Handles YouTube video downloading and processing."""
    
    @staticmethod
    @retry.Retry(
        predicate=retry.if_exception_type(
            google_exceptions.ServiceUnavailable,
            google_exceptions.DeadlineExceeded,
        )
    )
    def download_audio(url: str, keep_video: bool = False, video_quality: str = '720p') -> FileMetadata:
        """Download audio from YouTube URL."""
        try:
            # Configure yt-dlp options
            ydl_opts = {
                'format': f'bestvideo[ext=mp4][height<={video_quality[:-1]}]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': {
                    'default': os.path.join(
                        OUTPUT_FOLDER,
                        '%(title)s',
                        '%(title)s.%(ext)s'
                    )
                },
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'keepvideo': keep_video,
                'restrictfilenames': True,  # This handles special characters
                'windowsfilenames': True,   # This ensures cross-platform compatibility
                'quiet': True
            }

            # Single download operation
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_title = to_snake_case(str(info.get('title', '')))
                
                # Get output directory
                output_dir = os.path.join(OUTPUT_FOLDER, video_title)
                os.makedirs(output_dir, exist_ok=True)
                
                # Get file paths
                audio_file = os.path.join(output_dir, f"{video_title}.wav")
                video_file = os.path.join(output_dir, f"{video_title}.mp4") if keep_video else None
                
                # Verify files exist
                if not os.path.exists(audio_file):
                    raise YouTubeDownloadError(f"Audio file not found after download: {audio_file}")
                    
                # Get file sizes
                audio_size = os.path.getsize(audio_file)
                video_size = os.path.getsize(video_file) if video_file and os.path.exists(video_file) else 0
                
                # Extract metadata
                youtube_metadata = {
                    'title': video_title,
                    'author': str(info.get('uploader', '')),
                    'url': url,
                    'publish_date': str(info.get('upload_date', '')),
                    'views': int(info.get('view_count', 0)),
                    'duration': int(info.get('duration', 0))
                }

                return audio_file, audio_size, youtube_metadata, video_file, video_size

        except Exception as e:
            logger.error(f"Error downloading YouTube audio/video: {str(e)}")
            raise YouTubeDownloadError(f"Error downloading YouTube audio/video: {str(e)}")

class SpeechRecognizer:
    """Handles Google Cloud Speech-to-Text operations."""
    
    def __init__(self, project_id: str):
        """Initialize speech recognizer."""
        self.client = SpeechClient()
        self.project_id = project_id
        self.storage_client = storage.Client()
        
        # Create output bucket if it doesn't exist
        self.output_bucket_name = f"{project_id}-speech-output"
        self.output_bucket = self.storage_client.bucket(self.output_bucket_name)
        
        if not self.output_bucket.exists():
            try:
                # Create bucket with proper location
                self.output_bucket = self.storage_client.create_bucket(
                    self.output_bucket_name,
                    location="us-central1",  # Match Speech-to-Text region
                    uniform_bucket_level_access=True  # Enable uniform access
                )
                logger.info(f"Created output bucket: {self.output_bucket_name}")
                
                # Set IAM permissions with correct roles
                policy = self.output_bucket.get_iam_policy()
                
                # Use correct service account and roles
                service_account = f"service-{project_id}@gcp-sa-speech.iam.gserviceaccount.com"
                
                # Use only supported roles
                roles = [
                    "roles/storage.objectViewer",
                    "roles/storage.objectCreator"
                ]
                
                for role in roles:
                    member = f"serviceAccount:{service_account}"
                    policy.bindings.append({
                        "role": role,
                        "members": [member]
                    })
                
                self.output_bucket.set_iam_policy(policy)
                logger.info("Set IAM permissions for output bucket")
                
            except Exception as e:
                logger.error(f"Failed to create/configure bucket: {str(e)}")
                raise
    
    def create_recognition_config(self, audio_file: str) -> cloud_speech.RecognitionConfig:
        """Create v2 recognition config."""
        return cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=SPEECH_LANGUAGE_CODES,
            model="latest_long",  # v2 model name
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                enable_word_confidence=True,
                enable_spoken_punctuation=True,
                enable_spoken_emojis=True,
                multi_channel_mode="SEPARATE_RECOGNITION_PER_CHANNEL"  # v2 feature
            )
        )

class TranscriptProcessor:
    """Handles processing of transcription results."""
    
    def process_response(self, response_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process v2 API response."""
        try:
            if not response_dict.get('results'):
                raise TranscriptionError("No results in response")
            
            file_result = next(iter(response_dict['results'].values()))
            
            transcript_data = {
                "transcript": "",
                "confidence": 0.0,
                "words": [],
                "language_code": ""
            }
            
            if 'transcript' in file_result:
                results = file_result['transcript'].get('results', [])
                for result in results:
                    if 'alternatives' in result and result['alternatives']:
                        alt = result['alternatives'][0]
                        transcript_data["transcript"] += alt.get('transcript', '') + " "
                        transcript_data["confidence"] = max(
                            transcript_data["confidence"],
                            alt.get('confidence', 0.0)
                        )
                        if "words" in alt:
                            transcript_data["words"].extend(alt["words"])
                        transcript_data["language_code"] = result.get('languageCode', '')

            return transcript_data

        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            raise TranscriptionError(f"Error processing response: {str(e)}")

class FileManager:
    """Handles file management operations."""
    
    @staticmethod
    def cleanup_temp_files(directory: str, extensions: List[str] = SUPPORTED_AUDIO_EXTENSIONS) -> None:
        """
        Clean up temporary files in the given directory.
        
        Args:
            directory: Directory to clean
            extensions: File extensions to clean up
        """
        for ext in extensions:
            for file in glob.glob(os.path.join(directory, f"*{ext}")):
                try:
                    if not file.endswith('.wav'):
                        os.remove(file)
                        logger.info(f"Cleaned up temporary file: {file}")
                except OSError as e:
                    logger.warning(f"Could not remove file {file}: {e}")

def process_audio(
    file_path: str,
    is_youtube_url: bool = True,
    keep_video: bool = False,
    video_quality: str = '720p',
    custom_classes: Optional[List] = None,
    phrase_sets: Optional[List] = None,
    post_processor: Optional[GeminiPostProcessor] = None
) -> Dict[str, Any]:
    """Process audio file for transcription."""
    try:
        logger.debug(f"Starting audio processing for file: {file_path}")
        logger.debug(f"Parameters: is_youtube={is_youtube_url}, keep_video={keep_video}, quality={video_quality}")
        
        # Initialize components
        gcs_manager = GCSManager(GOOGLE_CLOUD_PROJECT)
        speech_recognizer = SpeechRecognizer(GOOGLE_CLOUD_PROJECT)
        transcript_processor = TranscriptProcessor()
        
        # Create post_processor if not provided
        if post_processor is None:
            post_processor = GeminiPostProcessor()
        
        # Download audio if needed
        audio_file, audio_size, youtube_metadata, video_file, video_size = (
            YouTubeDownloader.download_audio(file_path, keep_video, video_quality)
        )

        # Get output directory from audio file path
        output_dir = os.path.dirname(audio_file)
        logger.debug(f"Using output directory: {output_dir}")

        # Upload to GCS with chunked upload and retry
        logger.debug(f"Uploading to GCS: {audio_file}")
        gcs_uri = gcs_manager.upload_file(
            audio_file,
            chunk_size=5 * 1024 * 1024,  # 5MB chunks
            retry_config=retry_config
        )
        logger.debug(f"Uploaded to GCS: {gcs_uri}")

        # Create v2 recognition config
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=SPEECH_LANGUAGE_CODES,
            model="latest_long",  # Use latest long model for v2
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                enable_word_confidence=True
            )
        )

        # Create v2 batch recognition request
        request = cloud_speech.BatchRecognizeRequest(
            recognizer=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global/recognizers/_",
            config=config,
            files=[cloud_speech.BatchRecognizeFileMetadata(uri=gcs_uri)],
            recognition_output_config=cloud_speech.RecognitionOutputConfig(
                inline_response_config=cloud_speech.InlineOutputConfig()
            )
        )

        # Process with v2 operation monitoring
        operation = speech_recognizer.client.batch_recognize(request=request)
        
        logger.info("Speech-to-Text recognition request sent. Monitoring progress...")
        last_progress = -1
        while not operation.done():
            metadata = operation.metadata
            if hasattr(metadata, 'progress_percent'):
                progress = metadata.progress_percent
                if progress != last_progress:
                    logger.info(f"Transcription progress: {progress}%")
                    last_progress = progress
            time.sleep(10)  # Longer sleep for long audio

        # Get v2 results with proper timeout
        response = operation.result(timeout=600)
        response_dict = MessageToDict(response._pb)

        # Save raw response silently
        raw_response_path = os.path.join(
            output_dir,
            f"raw_api_response_{os.path.basename(audio_file)}.json"
        )
        with open(raw_response_path, "w") as f:
            json.dump(response_dict, f, indent=2)
            
        logger.info(f"Raw API response saved to: {raw_response_path}")

        # Process response using transcript processor
        transcript_data = transcript_processor.process_response(response_dict)
        
        # Save transcript silently
        transcript_path = os.path.join(output_dir, "transcript.txt")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript_data["transcript"])
            
        # Only log the path, not the content
        logger.info(f"Transcript saved to: {transcript_path}")

        # Save processed data silently
        processed_path = os.path.join(output_dir, "processed.json")
        with open(processed_path, "w") as f:
            json.dump(transcript_data, f, indent=2)
            
        # Create analysis file immediately after processing
        analysis_path = os.path.join(output_dir, f"{os.path.basename(output_dir)}_analysis.json")
        analysis_data = post_processor.process_transcript(
            transcript_data=transcript_data,
            description=youtube_metadata.get("description", ""),
            youtube_metadata=youtube_metadata
        )
        
        # Return all paths including analysis
        return {
            "paths": {
                "audio": audio_file,
                "video": video_file,
                "transcript": transcript_path,
                "raw_response": raw_response_path,
                "processed": processed_path,
                "analysis": analysis_path
            },
            "metadata": youtube_metadata,
            "sizes": {
                "audio": audio_size,
                "video": video_size
            }
        }

    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}", exc_info=True)
        raise AudioProcessingError(f"Error processing audio: {str(e)}")

class TranscriptionManager:
    """High-level manager for transcription operations."""
    
    def __init__(self, project_id: str = GOOGLE_CLOUD_PROJECT):
        """
        Initialize transcription manager.
        
        Args:
            project_id: Google Cloud project ID
        """
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT is not set in the config")
            
        self.project_id = project_id
        self.gcs_manager = GCSManager(project_id)
        self.speech_recognizer = SpeechRecognizer(project_id)
        self.transcript_processor = TranscriptProcessor()
        
    def process_youtube_video(
        self,
        url: str,
        keep_video: bool = False,
        video_quality: str = '720p',
        custom_classes: Optional[List] = None,
        phrase_sets: Optional[List] = None
    ) -> TranscriptionResult:
        """
        Process a YouTube video for transcription.
        
        Args:
            url: YouTube URL
            keep_video: Whether to keep video file
            video_quality: Video quality for download
            custom_classes: Custom classes for speech recognition
            phrase_sets: Phrase sets for speech recognition
            
        Returns:
            Transcription results and metadata
            
        Raises:
            YouTubeDownloadError: If download fails
            AudioProcessingError: If processing fails
        """
        return process_audio(
            url,
            is_youtube_url=True,
            keep_video=keep_video,
            video_quality=video_quality,
            custom_classes=custom_classes,
            phrase_sets=phrase_sets
        )
        
    def save_results(
        self,
        transcript_data: Dict[str, Any],
        output_dir: str,
        base_filename: str
    ) -> Tuple[str, str]:
        """
        Save transcription results to files.
        
        Args:
            transcript_data: Processed transcript data
            output_dir: Directory to save results
            base_filename: Base name for output files
            
        Returns:
            Tuple of paths to saved files
            
        Raises:
            IOError: If saving fails
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Save transcript
            transcript_path = os.path.join(output_dir, f"{base_filename}_transcript.txt")
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript_data["transcript"])
                
            # Save detailed results
            details_path = os.path.join(output_dir, f"{base_filename}_details.json")
            with open(details_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2)
                
            return transcript_path, details_path
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise IOError(f"Failed to save results: {str(e)}")

def save_raw_response(response: Any, filename: str, output_folder: str) -> str:
    """
    Save raw API response to file.
    
    Args:
        response: API response
        filename: Output filename
        output_folder: Output directory
        
    Returns:
        Path to saved file
        
    Raises:
        IOError: If saving fails
    """
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(output_folder, f"raw_api_response_{filename}.json")
    
    try:
        # Ensure response is serializable
        if isinstance(response, str):
            response_data = json.loads(response)
        else:
            response_data = (
                MessageToDict(response._pb)
                if hasattr(response, '_pb')
                else response
            )
            
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, default=str)
        return file_path
    except Exception as e:
        logger.error(f"Error saving raw API response: {e}")
        raise IOError(f"Failed to save raw response: {str(e)}")

# Optional: Add CLI interface if needed
if __name__ == "__main__":
    # Example usage
    manager = TranscriptionManager()
    url = input("Enter YouTube URL: ")
    try:
        results = manager.process_youtube_video(url)
        print(f"Transcription completed successfully: {results[0]['transcript'][:100]}...")
    except Exception as e:
        print(f"Error: {str(e)}")