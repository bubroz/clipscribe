# ClipScribe AI Assistant Continuation Prompt

## Current State (2025-07-20 22:54 PDT)

### Latest Version: v2.19.3
**Major Progress!** Pre-upload videos to GCS working perfectly. 19/20 test videos uploaded. Vertex AI GCS URI support added. Still need to fix the 400 Invalid Argument error.

### Recent Changes
- **v2.19.3** (2025-07-20): Pre-upload videos & Vertex AI improvements
  - ✅ Created `scripts/pre_upload_test_videos.py` - batch upload to GCS
  - ✅ Fixed video ID extraction bug (was getting "watch" for all youtube.com URLs)
  - ✅ Successfully uploaded 19/20 test videos (1 age-restricted failed)
  - ✅ Added `gcs_uri` parameter to VertexAITranscriber
  - ✅ Created comprehensive documentation: `docs/PRE_UPLOAD_VIDEOS.md`
  - ✅ Created `test_vertex_ai_gcs.py` for testing with pre-uploaded videos
  - ❌ Still getting 400 Invalid Argument error from Vertex AI
- **v2.19.2** (2025-07-20): Vertex AI SDK integration (90% complete)
- **v2.19.1** (2025-07-20): Fixed collection summary bug

### Pre-Upload Success ✅
```bash
# Successfully uploaded test videos:
✅ 15 new uploads + 4 already uploaded = 19 total
❌ 1 failed (age-restricted)
📦 Total size: ~2.1 GB
🚀 Ready for instant Vertex AI testing!
```

### What's Working Well ✅
- Regular Gemini API: Perfect at $0.0035/video
- Vertex AI authentication: Complete
- GCS uploads: Working perfectly
- Pre-upload tracking: Smart deduplication
- Video downloads: Fast and reliable

### The ONE Remaining Issue 🎯
```
400 Request contains an invalid argument.
```
This happens when calling Vertex AI with video content. Likely issues:
1. Prompt format mismatch between video/audio modes
2. Generation config parameters
3. Content type or MIME type issues

### Next Steps (for new chat) 🚀
1. **Debug 400 error** - Check prompt building logic in `_build_comprehensive_prompt`
2. **Test with GCS URIs** - Use pre-uploaded videos for faster iteration
3. **Compare prompts** - Log exact prompts for video vs audio mode
4. **Celebrate** when it works!

### Key Files to Check
- `src/clipscribe/retrievers/vertex_ai_transcriber.py` - line ~100 prompt building
- `scripts/test_vertex_ai_gcs.py` - new test script with GCS URIs
- `output/pre_uploaded_videos/upload_summary.json` - all GCS URIs

### GCS URIs Ready for Testing
```
gs://prismatic-iris-429006-g6-clipscribe-staging/videos/2025-07-20T22:12:47.166904/youtube video 6ZVj1_SE4Mo-6ZVj1_SE4Mo.mp4
gs://prismatic-iris-429006-g6-clipscribe-staging/videos/2025-07-20T22:40:58.589788/youtube video hj9rK35ucCc-hj9rK35ucCc.mp4
```