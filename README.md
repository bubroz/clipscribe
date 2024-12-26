# ClipScribe

ClipScribe is an advanced YouTube video transcription and analysis tool that combines state-of-the-art speech recognition with AI-powered post-processing to generate high-quality transcripts, summaries, and study materials. It focuses exclusively on YouTube video processing, integrating the powerful Gemini 1.5 Pro AI model for advanced post-processing capabilities.

## Project Status

ClipScribe is currently in advanced development but not yet fully functional. The core components, including transcription and post-processing with the Gemini model, have been implemented. However, several areas still need improvement:

- Web interface development
- Comprehensive automated testing
- AI model refinement and optimization
- Staging environment setup
- User authentication and management system
- Rate limiting and usage tracking implementation
- Detailed API documentation creation
- Report generation refinement

## Project Roadmap

1. **AI Model Integration**
   - Fully integrate Gemini 1.5 Pro model
   - Develop model-specific prompt engineering techniques
   - Implement adaptive model selection based on video content
   - Future enhancement: Integrate Claude Sonnet 3.5 model

2. **YouTube Processing Enhancements**
   - Improve YouTube video metadata extraction and utilization
   - Implement advanced video categorization and tagging system
   - Develop support for playlist and channel analysis

3. **Transcript Enhancement**
   - Implement advanced speaker diarization techniques for multi-speaker videos
   - Develop context-aware timestamp insertion for improved navigation
   - Create customizable transcript formatting options

4. **Analysis Capabilities**
   - Expand NLP capabilities for deeper content understanding and summarization
   - Implement cross-video topic analysis and trend detection
   - Develop visual content analysis integration (e.g., scene detection, object recognition)

5. **Performance Optimization**
   - Implement distributed processing for large-scale video analysis
   - Optimize caching mechanisms for improved response times
   - Develop adaptive resource allocation based on video complexity

6. **User Experience**
   - Create a web-based interface for easy video submission and result viewing
   - Implement customizable report generation with interactive elements
   - Develop API endpoints for integration with other applications

7. **Quality Assurance**
   - Expand test coverage to include edge cases and stress testing
   - Implement automated benchmarking for continuous performance monitoring
   - Develop a comprehensive error handling and recovery system

8. **Documentation and Training**
   - Create detailed API documentation and usage guides
   - Develop training materials for effectively using ClipScribe's advanced features
   - Implement a feedback system for continuous improvement

9. **Compliance and Ethics**
   - Ensure GDPR and CCPA compliance for user data handling
   - Implement ethical AI guidelines and bias detection mechanisms
   - Develop transparency reports for AI model decision-making processes

10. **Future Expansions**
    - Explore integration with additional video platforms beyond YouTube
    - Investigate real-time video analysis capabilities for live streams
    - Research potential applications in auto-generated content creation using AI models tuned for specific content types and styles using our reports as training data. Focus on educational, news, and entertainment content types.

## Features

Currently implemented features:
- Transcribe YouTube videos with high accuracy
- Generate comprehensive summaries and study guides using Gemini 1.5 Pro
- Advanced YouTube video downloading and processing
- Advanced NLP analysis including topic distribution, sentiment analysis, and argument identification
- Named Entity Recognition (NER) for improved content understanding
- Detailed language analysis including readability scores and linguistic metrics
- Integration with Google Cloud Speech-to-Text API v2 for accurate transcription
- Output in both JSON and text formats
- Comprehensive error handling and logging with detailed diagnostics
- Automatic file naming based on YouTube video titles
- Output organized in video-specific folders
- Basic report generation using Gemini 1.5 Pro

Features in development:
- Implement retention of original .webm files
- Organize output files in folders named after video titles within the `src/output` directory
- Create in-depth review questions and quizzes
- Speaker diarization for multi-speaker videos
- Language detection and support for multiple languages
- Prompt optimization and caching for improved performance
- Automated benchmarking for continuous performance tracking
- Distributed processing for large-scale video analysis
- Adaptive resource allocation based on video complexity
- GDPR and CCPA compliance for user data handling
- Ethical AI guidelines and bias detection mechanisms
- Refine and expand report generation capabilities

## Requirements

- Python 3.9+
- Google Cloud account with Speech-to-Text API v2 enabled
- Google Cloud credentials (JSON key file)
- Gemini 1.5 Pro API key
- yt-dlp (for YouTube video downloading)
- FFmpeg (for video processing)
- nltk
- spacy
- textstat
- textblob
- google-cloud-speech==2.0.0 or later
- google-cloud-storage
- python-dotenv
- google-generativeai (for Gemini API)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/clipscribe.git
   cd clipscribe
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Download the spaCy English model:
   ```
   python -m spacy download en_core_web_sm
   ```

5. Set up your environment variables:
   Create a `.env` file in the project root and add the following:
   ```
   GOOGLE_CLOUD_PROJECT=your_project_id
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   GEMINI_API_KEY=your_gemini_api_key
   ```

6. Install FFmpeg:
   - On macOS (using Homebrew): `brew install ffmpeg`
   - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - On Windows: Download from https://ffmpeg.org/download.html and add to PATH

7. Verify the installation:
   ```
   python src/clipscribe.py --version
   ```

Note: The test suite and pre-commit hooks are not yet fully implemented.

## Quick Start

1. Activate your virtual environment:
   ```
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Run ClipScribe:
   ```
   python src/clipscribe.py
   ```

3. When prompted, enter a YouTube URL.

4. Wait for the processing to complete. Output files, including the generated report, will be in the `output` directory.

## Usage

1. Run the main script:
   ```
   python src/clipscribe.py
   ```
2. Enter the YouTube URL when prompted.
3. The script will process the video using Gemini 1.5 Pro, generate output files, and create a basic report.

Example output:
```
Enter YouTube URL: https://www.youtube.com/watch?v=rFZrL1RiuVI
Processing YouTube video...
Transcription progress: 100%
Analysis complete. Saving output files...
Processing completed successfully
Processed text transcript saved to: output/never_gonna_give_you_up/never_gonna_give_you_up_processed.json
Raw API response saved to: output/never_gonna_give_you_up/raw_api_response.json
Basic report saved to: output/never_gonna_give_you_up/report.md

YouTube Video Metadata:
Title: Rick Astley - Never Gonna Give You Up (Official Music Video)
Author: Rick Astley
Publish Date: 2009-10-25
Views: 1234567890
Duration: 213
```

Output files are generated in a video-specific folder within the `output` directory:
- `<video_title>_processed.json`: Full analysis results
- `<video_title>_summary.md`: Formatted summary with transcript, analysis, and key insights
- `raw_api_response.json`: Raw API response from the transcription service
- `report.md`: Basic report generated using Gemini 1.5 Pro

Features:
- Processes public YouTube videos
- Automatic file naming based on video titles
- Output in JSON and Markdown formats
- Transcripts with MM:SS timestamps
- Advanced NLP analysis (topic modeling, sentiment analysis, named entity recognition, etc.)

Note: If automatic YouTube audio downloading fails, manual download instructions will be provided.

## Troubleshooting

1. **YouTube Download Fails**
   - Update yt-dlp: `pip install --upgrade yt-dlp`
   - Use manual download instructions if provided
   - Check internet connection and YouTube availability

2. **Audio Transcription Errors**
   - Verify Google Cloud credentials in `.env` file
   - Check `GOOGLE_CLOUD_PROJECT` and `GOOGLE_APPLICATION_CREDENTIALS` environment variables
   - Review `transcription.log` for error messages
   - Ensure Speech-to-Text API is enabled in Google Cloud Console

3. **AI Model Processing Issues**
   - Verify API key for Gemini in `.env` file
   - Check `post_processing.log` for error details
   - Ensure internet connectivity for AI services
   - Verify API rate limits and quotas

4. **ImportError or ModuleNotFoundError**
   - Activate virtual environment
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Try creating a new virtual environment if issues persist

5. **FFmpeg Related Errors**
   - Verify FFmpeg installation and system PATH
   - Restart terminal after installation (Windows)
   - Run `ffmpeg -version` to check installation

6. **Transcript Timing Issues**
   - 'start_time' field removed from transcript segments
   - Timing based on 'end_time' field only

7. **Output File Issues**
   - Check write permissions for `output` directory
   - Avoid spaces and special characters in video titles

8. **Performance Issues**
   - Ensure system meets minimum requirements for long videos
   - Consider processing shorter video segments if needed

For detailed troubleshooting, check log files in the project directory. If issues persist, open a GitHub issue with:
- Error message and stack trace
- ClipScribe version
- Python version
- Operating system
- Steps to reproduce the issue

## Contributing

We welcome contributions to the ClipScribe project! As we are in active development, we particularly appreciate help in the following areas:

- Developing the web-based user interface
- Implementing comprehensive automated tests
- Refining and optimizing AI model interactions
- Setting up a staging environment for testing
- Developing the user authentication and management system
- Implementing rate limiting and usage tracking
- Creating detailed API documentation

If you're interested in contributing, please open an issue to discuss your ideas before submitting a pull request. We'll provide more detailed contribution guidelines as the project matures.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Cloud Speech-to-Text API
- Google Gemini API
- yt-dlp for YouTube video downloading
- spaCy for Named Entity Recognition

## Support

For support:
1. Check the troubleshooting section in this README
2. Review the log files in the project directory
3. Open an issue in the GitHub repository
4. Contact the maintainers directly at support@clipscribe.com

---

**Note**: This project is for educational and research purposes only. Ensure you comply with all applicable laws and terms of service when using this tool.