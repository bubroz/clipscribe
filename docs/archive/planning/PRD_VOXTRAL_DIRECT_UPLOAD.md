# PRD: Direct File Upload Optimization for Voxtral

**Version:** 1.0  
**Date:** September 6, 2025  
**Status:** Planning

## Executive Summary

Optimize Voxtral transcription by eliminating the intermediate signed URL step, reducing API calls from 4 to 1 and improving processing speed by ~30%.

## Problem Statement

Current workflow is inefficient:
1. Upload file to Mistral (API call #1)
2. Get signed URL (API call #2) 
3. Transcribe using URL (API call #3)
4. Delete file (API call #4)

This adds unnecessary latency and complexity.

## Solution Overview

Send audio file directly in the transcription request, eliminating intermediate steps.

## Technical Specification

### Current Implementation (Inefficient)
```python
file_id = await self._upload_file(session, audio_path)
signed_url = await self._get_signed_url(session, file_id)
result = await self._transcribe_with_url(session, signed_url)
await self._delete_file(session, file_id)
```

### Optimized Implementation
```python
async def transcribe_direct(self, audio_path: Path) -> Dict:
    """Direct file upload in transcription request."""
    url = f"{self.BASE_URL}/audio/transcriptions"
    
    with open(audio_path, 'rb') as audio_file:
        data = aiohttp.FormData()
        data.add_field('file', audio_file, 
                      filename=audio_path.name,
                      content_type=self._get_mime_type(audio_path))
        data.add_field('model', self.model)
        data.add_field('temperature', '0.0')
        # ... other parameters
        
        async with session.post(url, data=data) as response:
            return await response.json()
```

## Performance Impact

| Metric | Current | Optimized | Improvement |
|--------|---------|-----------|-------------|
| API Calls | 4 | 1 | **75% reduction** |
| Latency | ~3s overhead | ~0s | **3s faster** |
| Error Points | 4 | 1 | **75% reduction** |
| Code Complexity | High | Low | **Simpler** |

## Implementation Plan

### Phase 1: Research
- Verify Mistral API supports direct file upload
- Test with small audio files
- Measure performance improvement

### Phase 2: Implementation
- Create new `transcribe_direct` method
- Add fallback to signed URL approach
- Update chunking to use direct upload

### Phase 3: Migration
- Switch primary path to direct upload
- Keep signed URL as fallback
- Monitor error rates

## Success Metrics

- **Speed:** 30% faster transcription
- **Reliability:** 50% fewer timeout errors
- **Simplicity:** 75% less code
- **Cost:** Same (no pricing change)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| File size limits | High | Chunk large files |
| Memory usage | Medium | Stream file upload |
| API compatibility | High | Keep signed URL fallback |

## Acceptance Criteria

- [ ] Direct upload method implemented
- [ ] 30% speed improvement verified
- [ ] Fallback mechanism in place
- [ ] All file types supported
- [ ] Memory efficient for large files
