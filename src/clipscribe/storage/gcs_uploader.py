"""
Upload X drafts to Google Cloud Storage for mobile access.

Creates mobile-optimized HTML pages for reviewing drafts.
Handles 72-hour auto-deletion of videos.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
from google.cloud import storage
from ..utils.text_utils import clean_for_display
from datetime import timedelta

logger = logging.getLogger(__name__)


def generate_draft_page(
    executive_summary: str,
    tweet_styles: dict,
    video_title: str,
    video_url: str,
    entities: list,
    relationships: list,
    thumbnail_filename: str = "thumbnail.jpg",
    video_filename: str = "video.mp4"
) -> str:
    """
    Generate mobile-optimized HTML page for draft review.
    
    Optimized for Pixel 9 Pro:
    - One-tap copy
    - Easy media download
    - Clean, fast interface
    """
    
    # Create safe download filenames from video title
    import re
    safe_title = re.sub(r'[^\w\s-]', '', video_title)[:50]  # Remove special chars, limit length
    safe_title = re.sub(r'[-\s]+', '_', safe_title).strip('_')  # Spaces to underscores
    
    thumbnail_download_name = f"{safe_title}_thumbnail.jpg"
    video_download_name = f"{safe_title}.mp4"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Draft - {video_title[:50]}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #000;
            color: #fff;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 20px;
            margin-bottom: 10px;
        }}
        .stats {{
            color: #71767b;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .tweet-box {{
            background: #16181c;
            border: 1px solid #2f3336;
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 20px;
        }}
        #tweet-text {{
            font-size: 16px;
            line-height: 1.5;
            margin-bottom: 12px;
            white-space: pre-wrap;
        }}
        .char-count {{
            color: #71767b;
            font-size: 14px;
            margin-bottom: 12px;
        }}
        button, a.download-btn {{
            background: #1d9bf0;
            color: #fff;
            border: none;
            border-radius: 24px;
            padding: 12px 24px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-bottom: 12px;
            display: block;
            text-align: center;
            text-decoration: none;
        }}
        button:active, a.download-btn:active {{
            background: #1a8cd8;
        }}
        .media-section {{
            margin-top: 20px;
        }}
        .media-item {{
            background: #16181c;
            border: 1px solid #2f3336;
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 16px;
        }}
        img, video {{
            max-width: 100%;
            border-radius: 12px;
            display: block;
            margin: 12px 0;
        }}
        .success {{
            background: #00ba7c;
            color: #fff;
            padding: 12px;
            border-radius: 8px;
            margin-top: 12px;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{video_title}</h1>
        <div class="stats">
            📊 {len(entities)} entities • {len(relationships)} relationships
        </div>
        
        <div class="tweet-box">
            <h3>Executive Summary</h3>
            <div style="line-height: 1.6; margin-bottom: 20px; white-space: pre-wrap;">
                {clean_for_display(executive_summary, max_length=2000)}
            </div>
        </div>
        
        <div class="tweet-box">
            <h3>📊 Key Entities</h3>
            <div style="font-size: 14px; line-height: 1.8;">
                {''.join([f'<div>• {e.get("name") if isinstance(e, dict) else getattr(e, "name", "")} <span style="color: #71767b;">({e.get("type") if isinstance(e, dict) else getattr(e, "type", "")})</span></div>' for e in entities[:15]])}
            </div>
        </div>
        
        <div class="tweet-box">
            <h3>🔗 Key Relationships</h3>
            <div style="font-size: 14px; line-height: 1.8;">
                {''.join([f'<div>• {r.get("subject") if isinstance(r, dict) else getattr(r, "subject", "")} → {r.get("predicate") if isinstance(r, dict) else getattr(r, "predicate", "")} → {r.get("object") if isinstance(r, dict) else getattr(r, "object", "")}</div>' for r in relationships[:10]])}
            </div>
        </div>
        
        <h2 style="margin-top: 30px; margin-bottom: 16px;">Pick Your Style:</h2>
        
        <!-- Style 1: The Analyst -->
        <div class="tweet-box">
            <div style="color: #71767b; font-size: 14px; margin-bottom: 8px;">📊 The Analyst</div>
            <div id="tweet-analyst" style="margin-bottom: 12px;">{tweet_styles.get('analyst', 'Generating...')}</div>
            <div class="char-count">{len(tweet_styles.get('analyst', ''))} / 280 characters</div>
            <div style="margin-bottom: 8px;">
                <input type="checkbox" id="video-analyst" style="margin-right: 8px;">
                <label for="video-analyst" style="color: #71767b; font-size: 14px;">Include video</label>
            </div>
            <button onclick="shareTweet('analyst')">📱 Share</button>
        </div>
        
        <!-- Style 2: The Alarm -->
        <div class="tweet-box">
            <div style="color: #71767b; font-size: 14px; margin-bottom: 8px;">⚡ The Alarm</div>
            <div id="tweet-alarm" style="margin-bottom: 12px;">{tweet_styles.get('alarm', 'Generating...')}</div>
            <div class="char-count">{len(tweet_styles.get('alarm', ''))} / 280 characters</div>
            <div style="margin-bottom: 8px;">
                <input type="checkbox" id="video-alarm" style="margin-right: 8px;">
                <label for="video-alarm" style="color: #71767b; font-size: 14px;">Include video</label>
            </div>
            <button onclick="shareTweet('alarm')">📱 Share</button>
        </div>
        
        <!-- Style 3: The Educator -->
        <div class="tweet-box">
            <div style="color: #71767b; font-size: 14px; margin-bottom: 8px;">📚 The Educator</div>
            <div id="tweet-educator" style="margin-bottom: 12px;">{tweet_styles.get('educator', 'Generating...')}</div>
            <div class="char-count">{len(tweet_styles.get('educator', ''))} / 280 characters</div>
            <div style="margin-bottom: 8px;">
                <input type="checkbox" id="video-educator" style="margin-right: 8px;">
                <label for="video-educator" style="color: #71767b; font-size: 14px;">Include video</label>
            </div>
            <button onclick="shareTweet('educator')">📱 Share</button>
        </div>
        
        <div class="media-section">
            <div class="media-item">
                <h3>🖼️ Thumbnail</h3>
                <img src="{thumbnail_filename}" alt="Thumbnail" id="thumbnail">
                <a href="{thumbnail_filename}" download="{thumbnail_download_name}" class="download-btn">
                    ⬇️ Download
                </a>
                <button onclick="shareImage()">📤 Share</button>
            </div>
            
            <div class="media-item">
                <h3>🎥 Video</h3>
                <video src="{video_filename}" controls id="video"></video>
                <a href="{video_filename}" download="{video_download_name}" class="download-btn">
                    ⬇️ Download
                </a>
                <button onclick="shareVideo()">📤 Share</button>
            </div>
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #71767b; font-size: 14px;">
            Generated by ClipScribe v2.53.0
        </div>
    </div>
    
    <script>
        const videoUrl = "{video_url}";  // YouTube URL
        
        async function shareTweet(style) {{
            const tweetText = document.getElementById('tweet-' + style).innerText;
            const fullText = tweetText + '\\n\\n' + videoUrl;
            const includeVideo = document.getElementById('video-' + style).checked;
            
            try {{
                if (navigator.share) {{
                    const shareData = {{
                        text: fullText
                    }};
                    
                    if (includeVideo) {{
                        // Share with video
                        const videoBlob = await fetch('{video_filename}').then(r => r.blob());
                        const videoFile = new File([videoBlob], '{video_download_name}', {{ type: 'video/mp4' }});
                        shareData.files = [videoFile];
                    }} else {{
                        // Share with thumbnail
                        const thumbBlob = await fetch('{thumbnail_filename}').then(r => r.blob());
                        const thumbFile = new File([thumbBlob], '{thumbnail_download_name}', {{ type: 'image/jpeg' }});
                        shareData.files = [thumbFile];
                    }}
                    
                    await navigator.share(shareData);
                }} else {{
                    // Fallback: copy text
                    navigator.clipboard.writeText(fullText);
                    alert('Text copied! Open X app to paste and attach media.');
                }}
            }} catch (err) {{
                console.error('Share failed:', err);
                // Fallback
                navigator.clipboard.writeText(fullText);
                alert('Text copied! Open X app to paste.');
            }}
        }}
        
        async function shareImage() {{
            try {{
                const response = await fetch('{thumbnail_filename}');
                const blob = await response.blob();
                const file = new File([blob], '{thumbnail_download_name}', {{ type: 'image/jpeg' }});
                
                if (navigator.share) {{
                    await navigator.share({{
                        files: [file]
                    }});
                }}
            }} catch (err) {{
                // Fallback: download
                window.location.href = '{thumbnail_filename}';
            }}
        }}
        
        async function shareVideo() {{
            try {{
                // For large videos, just open in new tab for download
                // Fetching entire video in browser can timeout
                if (navigator.share) {{
                    // Share just the URL for videos (too large to fetch)
                    await navigator.share({{
                        title: '{video_title}',
                        url: window.location.href
                    }});
                }} else {{
                    // Fallback: direct download link
                    window.location.href = '{video_filename}';
                }}
            }} catch (err) {{
                console.error('Share failed:', err);
                // Force download
                window.location.href = '{video_filename}';
            }}
        }}
    </script>
</body>
</html>"""
    
    return html


class GCSUploader:
    """
    Upload X drafts to Google Cloud Storage.
    
    Features:
    - Mobile-optimized HTML pages
    - Public URLs for Telegram links
    - 72-hour auto-deletion
    - Thumbnail + video hosting
    """
    
    def __init__(self, bucket_name: str = "clipscribe-drafts"):
        """
        Initialize GCS uploader.
        
        Args:
            bucket_name: GCS bucket name
        """
        self.bucket_name = bucket_name
        
        try:
            # Use Application Default Credentials (ADC)
            self.client = storage.Client(project="prismatic-iris-429006-g6")
            self.bucket = self.client.bucket(bucket_name)
            
            # Set 72-hour lifecycle rule
            self.bucket.add_lifecycle_delete_rule(age=3)  # 3 days
            self.bucket.patch()
            
            logger.info(f"GCSUploader initialized: {bucket_name}")
        except Exception as e:
            logger.error(f"GCS initialization failed: {e}")
            self.bucket = None
    
    async def upload_draft(
        self,
        draft_id: str,
        executive_summary: str,
        tweet_styles: dict,
        video_title: str,
        video_url: str,
        entities: list,
        relationships: list,
        thumbnail_path: Optional[Path],
        video_path: Optional[Path]
    ) -> Optional[str]:
        """
        Upload complete draft to GCS.
        
        Returns:
            URL to draft review page
        """
        if not self.bucket:
            logger.warning("GCS not configured, skipping upload")
            return None
        
        try:
            logger.info(f"Starting GCS upload for draft: {draft_id}")
            
            # Generate HTML page
            html = generate_draft_page(
                executive_summary=executive_summary,
                tweet_styles=tweet_styles,
                video_title=video_title,
                video_url=video_url,
                entities=entities,
                relationships=relationships
            )
            logger.debug(f"Generated HTML page: {len(html)} chars")
            
            # Upload HTML (with retry)
            blob_html = self.bucket.blob(f"drafts/{draft_id}/index.html")
            logger.info(f"Uploading HTML to: {blob_html.name}")
            for attempt in range(3):
                try:
                    blob_html.upload_from_string(html, content_type="text/html", timeout=120)
                    logger.info(f"HTML uploaded successfully")
                    break
                except Exception as e:
                    logger.warning(f"HTML upload attempt {attempt + 1}/3 failed: {e}")
                    if attempt == 2:
                        raise  # Critical - page needs HTML
            
            # Upload thumbnail if exists (with retry)
            if thumbnail_path and thumbnail_path.exists():
                blob_thumb = self.bucket.blob(f"drafts/{draft_id}/thumbnail.jpg")
                logger.info(f"Uploading thumbnail: {thumbnail_path}")
                for attempt in range(3):
                    try:
                        blob_thumb.upload_from_filename(str(thumbnail_path), timeout=120)
                        logger.info(f"Thumbnail uploaded successfully")
                        break
                    except Exception as e:
                        logger.warning(f"Thumbnail upload attempt {attempt + 1}/3 failed: {e}")
                        if attempt == 2:
                            logger.error(f"Thumbnail upload failed after 3 attempts, continuing without thumbnail")
            
            # Upload video if exists (with retry, graceful failure)
            if video_path and video_path.exists():
                blob_video = self.bucket.blob(f"drafts/{draft_id}/video.mp4")
                logger.info(f"Uploading video: {video_path}")
                
                # Retry video upload (it's large and can timeout)
                for attempt in range(3):
                    try:
                        blob_video.upload_from_filename(str(video_path), timeout=300)
                        logger.info(f"Video uploaded successfully")
                        break
                    except Exception as e:
                        logger.warning(f"Video upload attempt {attempt + 1}/3 failed: {e}")
                        if attempt == 2:
                            logger.error(f"Video upload failed after 3 attempts, continuing without video")
                            # Continue anyway - page will work without video
            
            # Return public URL
            draft_url = blob_html.public_url
            logger.info(f"All files uploaded. Draft URL: {draft_url}")
            
            return draft_url
            
        except Exception as e:
            logger.error(f"Failed to upload draft to GCS: {e}", exc_info=True)
            return None


async def test_uploader():
    """Test GCS upload with sample draft."""
    uploader = GCSUploader()
    
    url = await uploader.upload_draft(
        draft_id="test_123",
        tweet_text="Test tweet text here...",
        video_title="Test Video",
        entity_count=10,
        relationship_count=5,
        thumbnail_path=None,
        video_path=None
    )
    
    print(f"Draft URL: {url}")


if __name__ == "__main__":
    asyncio.run(test_uploader())

