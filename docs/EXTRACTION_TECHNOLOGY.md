ClipScribe's intelligence extraction is a hybrid system that leverages the best of local and cloud-based models. The core of our high-quality, cost-effective extraction is **Google's Gemini 2.5 model family**.

- **Gemini 2.5 Flash**: Used for the majority of high-volume tasks, including transcription and standard entity/relationship extraction. It provides an optimal balance of speed, cost, and capability.
- **Gemini 2.5 Pro**: Reserved for complex, high-reasoning tasks such as multi-video collection synthesis and knowledge graph cleaning.

All prompts optimized for completeness without arbitrary limits. We exclusively use the 2.5 generation models to ensure we are always leveraging the latest technology. We do not use older models like 1.5.

## Large Video Processing: The "Smart Transcribe, Global Analyze" Method

For videos longer than 15 minutes, ClipScribe employs a sophisticated, two-phase architecture to ensure both speed and maximum analytical quality:

**Phase 1: Parallel Raw Transcription**
1.  **Split with Overlap**: The source video is intelligently split into 10-minute chunks with a 30-second overlap to ensure no words are lost at the seams.
2.  **Parallel Transcription**: Each chunk is transcribed to raw text in parallel. This step is optimized for speed and fault tolerance.

**Phase 2: Global Intelligence Analysis**
1.  **Intelligent Merging**: The raw transcripts from all chunks are stitched together. A sequence matching algorithm is used to analyze the 30-second overlaps, remove duplicate sentences, and produce a single, perfectly coherent transcript of the entire video.
2.  **Global Analysis**: A single, powerful intelligence extraction call is made to the Gemini 2.5 Pro model using the complete, merged transcript.

This method provides the best of both worlds: the speed of parallel processing and the superior analytical quality that only comes from analyzing the full context of the video in a single pass. This avoids the catastrophic loss of context that would occur from analyzing each chunk in isolation. 