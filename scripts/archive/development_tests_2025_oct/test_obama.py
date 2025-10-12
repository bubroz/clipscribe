#!/usr/bin/env python3
"""
Test with Obama's farewell address - EXACT example from Mistral documentation.
"""

import os
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_obama():
    """Test with the exact audio from documentation example."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        return
    
    test_audio = Path("obama_farewell.mp3")
    if not test_audio.exists():
        print(f"Test audio not found: {test_audio}")
        return
    
    print("=" * 60)
    print("TESTING WITH OBAMA'S FAREWELL ADDRESS")
    print("This is the EXACT example from Mistral documentation")
    print("=" * 60)
    print(f"\nAudio file: {test_audio} ({test_audio.stat().st_size / 1024:.1f} KB)")
    
    async with aiohttp.ClientSession() as session:
        # Upload file
        print("\n1. Uploading Obama farewell address...")
        url = "https://api.mistral.ai/v1/files"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        data = aiohttp.FormData()
        with open(test_audio, 'rb') as f:
            file_content = f.read()
        data.add_field('file', file_content, filename=test_audio.name, content_type='audio/mpeg')
        data.add_field('purpose', 'audio')
        
        async with session.post(url, headers=headers, data=data) as response:
            if response.status != 200:
                print(f"Upload failed: {response.status}")
                return
            upload_result = await response.json()
            file_id = upload_result["id"]
            print(f"   ✅ Uploaded: {file_id}")
        
        # Get signed URL
        print("\n2. Getting signed URL...")
        url = f"https://api.mistral.ai/v1/files/{file_id}/url"
        params = {"expiry": "24"}
        
        async with session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                print(f"Failed to get signed URL: {response.status}")
                return
            url_result = await response.json()
            signed_url = url_result["url"]
            print(f"   ✅ Got signed URL")
        
        # Transcribe with verbose_json
        print("\n3. Transcribing with verbose_json format...")
        print("   (This should return segments according to docs)")
        
        transcription_url = "https://api.mistral.ai/v1/audio/transcriptions"
        headers = {"x-api-key": api_key}
        
        data = aiohttp.FormData()
        data.add_field("model", "voxtral-mini-2507")
        data.add_field("file_url", signed_url)
        data.add_field("response_format", "verbose_json")
        
        async with session.post(transcription_url, headers=headers, data=data) as response:
            if response.status != 200:
                error = await response.text()
                print(f"   ❌ Failed: {response.status}")
                print(f"   Error: {error}")
                return
            
            result = await response.json()
            print(f"   ✅ Transcription successful!")
            
            print("\n4. RESPONSE ANALYSIS:")
            print("   " + "-" * 40)
            print(f"   Model: {result.get('model', 'N/A')}")
            print(f"   Language: {result.get('language', 'N/A')}")
            print(f"   Text length: {len(result.get('text', ''))} chars")
            
            # Check for segments
            if "segments" in result:
                segments = result["segments"]
                print(f"\n   SEGMENTS: {len(segments)}")
                
                if segments:
                    print("\n   🎯 SUCCESS! SEGMENTS FOUND!")
                    print("\n   First 5 segments:")
                    for i, seg in enumerate(segments[:5]):
                        print(f"\n   [{i}] Time: {seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s")
                        text = seg.get('text', '')
                        print(f"       Text: {text[:100]}{'...' if len(text) > 100 else ''}")
                    
                    # Compare with documentation example
                    print("\n   COMPARING WITH DOCUMENTATION EXAMPLE:")
                    doc_first_segment = "Four years ago, I came to Chicago to deliver my final farewell address to the nation, following"
                    our_first_segment = segments[0].get('text', '') if segments else ""
                    
                    if doc_first_segment in our_first_segment or our_first_segment in doc_first_segment:
                        print("   ✅ MATCHES documentation example!")
                    else:
                        print("   ⚠️  Different from documentation")
                        print(f"   Doc: {doc_first_segment[:50]}...")
                        print(f"   Our: {our_first_segment[:50]}...")
                else:
                    print("   ❌ Segments field exists but is EMPTY")
                    print("   This is the problem we're seeing!")
            else:
                print("   ❌ No segments field in response at all")
            
            # Check usage
            if "usage" in result:
                usage = result["usage"]
                print(f"\n   Usage:")
                print(f"      Audio seconds: {usage.get('prompt_audio_seconds', 0)}")
                print(f"      Total tokens: {usage.get('total_tokens', 0)}")
            
            # Save response
            with open("obama_response.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n   Full response saved to: obama_response.json")
            
            # Show sample of transcribed text
            if result.get('text'):
                print(f"\n   Sample of transcribed text:")
                print(f"   {result['text'][:200]}...")
        
        # Clean up
        print("\n5. Cleaning up...")
        url = f"https://api.mistral.ai/v1/files/{file_id}"
        async with session.delete(url, headers={"Authorization": f"Bearer {api_key}"}) as response:
            print(f"   File deleted: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_obama())
