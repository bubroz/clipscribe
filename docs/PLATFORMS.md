# Supported Platforms

*Last Updated: August 8, 2025*

ClipScribe supports **1800+ video platforms** through yt-dlp integration. If a video platform exists on the internet, there's a good chance ClipScribe can process it!

## Quick Check

To check if a specific URL is supported:

```bash
# Using ClipScribe
clipscribe --debug process video "YOUR_URL_HERE"

# Or test directly with Python
from clipscribe.retrievers.universal_video_client import UniversalVideoClient

client = UniversalVideoClient()
if client.is_supported_url("https://example.com/video"):
    print(" Supported!")
else:
    print(" Not supported")
```

## Popular Platforms

Here are some of the most commonly used platforms:

### Social Media

- **YouTube** - Including Shorts, Music, and Live streams
- **Twitter/X** - Video tweets and Spaces recordings
- **TikTok** - Short-form videos
- **Instagram** - Posts, Reels, IGTV
- **Facebook** - Videos, Live streams, Watch
- **Reddit** - Video posts
- **LinkedIn** - Native videos

### Video Hosting

- **Vimeo** - Professional video hosting
- **Dailymotion** - General video platform
- **Wistia** - Business video hosting
- **Streamable** - Quick video sharing
- **Imgur** - GIFs and videos
- **Gfycat** - GIF hosting

### Streaming Platforms

- **Twitch** - Gaming and live streams
- **Kick** - Live streaming
- **Rumble** - Video platform
- **Odysee** - Decentralized video

### News & Media

- **BBC** - BBC News, iPlayer
- **CNN** - News videos
- **NBC** - News and shows
- **ABC News** - News content
- **Reuters** - News videos
- **The Guardian** - Video content
- **Vice** - Documentary videos

### Educational

- **TED** - TED Talks
- **Khan Academy** - Educational videos
- **Coursera** - Course videos
- **MIT OpenCourseWare** - Lectures
- **Udemy** - Course previews

### Entertainment

- **Netflix** - Trailers and previews
- **Hulu** - Clips and trailers
- **Crunchyroll** - Anime previews
- **Funimation** - Anime content
- **Adult Swim** - Shows and clips

### Music & Audio

- **SoundCloud** - Music and podcasts
- **Bandcamp** - Artist uploads
- **Mixcloud** - DJ mixes and radio shows
- **Audiomack** - Music streaming

### International Platforms

- **Bilibili** - Chinese video platform
- **Niconico** - Japanese video platform
- **VK** - Russian social media videos
- **Weibo** - Chinese social media
- **Douyin** - Chinese TikTok

## Technical Details

ClipScribe uses yt-dlp as its backend for video extraction, which provides several advantages:

## Usage Examples

### Basic Usage

```python
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever

retriever = VideoIntelligenceRetriever()

# Process any supported URL
result = await retriever.process_url("https://example.com/video")
```

### Checking URL Support

```python
from clipscribe.retrievers.universal_video_client import UniversalVideoClient

client = UniversalVideoClient()

# Check if a URL is supported
if client.is_supported_url("https://example.com/video"):
    print(" This site is supported!")
else:
    print(" This site is not supported")
```

### Getting List of Supported Sites

```python
# Get a list of all supported site names
sites = client.get_supported_sites()
print(f"Total supported sites: {len(sites)}")
print("Some examples:", sites[:10])
```

## Authentication

Some sites require authentication. You can provide cookies or credentials:

### Using Browser Cookies

1. Install browser extension to export cookies
2. Export cookies.txt from your browser
3. Place in project directory
4. yt-dlp will automatically use them

### Direct Authentication

Some sites support username/password:

```python
# Configure in yt_dlp options
self.ydl_opts = {
    'username': 'your_username',
    'password': 'your_password',
    # ... other options
}
```

## Handling Private/Protected Content

### Password-Protected Videos

Many sites support password-protected videos:

- Vimeo: Add password to URL or use `videopassword` option
- Other sites: Check yt-dlp documentation for site-specific methods

### Age-Restricted Content

- YouTube: Requires cookies from logged-in session
- Other sites: Usually requires authentication

### Geo-Restricted Content

- Use VPN or proxy
- Configure proxy in yt_dlp options

## Performance Tips

1. **Keep yt-dlp Updated**: New sites are added regularly

   ```bash
   pip install -U yt-dlp
   ```

2. **Use Caching**: Our implementation caches processed videos to avoid re-downloading

3. **Error Handling**: Some sites may have temporary issues or rate limits

4. **Format Selection**: yt-dlp automatically selects the best available format

## Limitations

- **DRM-Protected Content**: Cannot download content protected by DRM (e.g., Netflix movies, Spotify songs)
- **Live Streams**: Limited support, depends on the platform
- **Paid Content**: Requires valid subscription/authentication
- **Rate Limits**: Some sites impose download limits

## Troubleshooting

### Common Issues

1. **"Unsupported URL"**
   - Check if URL is correct
   - Update yt-dlp: `pip install -U yt-dlp`
   - Some sites may change their structure

2. **"403 Forbidden" or "429 Too Many Requests"**
   - Site may have rate limits
   - Try using different IP or waiting
   - May need authentication

3. **"No video formats found"**
   - Video might be private or deleted
   - May require authentication
   - Could be geo-restricted

### Debug Mode

Enable verbose output to see what's happening:

```python
self.ydl_opts = {
    'verbose': True,
    # other options...
}
```

## Contributing

Found a site that doesn't work?

1. First update yt-dlp: `pip install -U yt-dlp`
2. Check if it works directly with yt-dlp command line
3. Report to yt-dlp project if it's a yt-dlp issue
4. Report to us if it's a ClipScribe integration issue

Remember: The power of ClipScribe comes from yt-dlp's extensive site support. As yt-dlp adds new sites, ClipScribe automatically gains support for them!

## Enterprise Scaling

Supports 1800+ platforms at scale with Vertex AI
