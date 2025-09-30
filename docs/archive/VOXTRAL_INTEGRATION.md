# Voxtral Integration Documentation

*Last Updated: 2025-09-05*
*Status: IMPLEMENTED - Production Ready*

## Overview

Voxtral is Mistral's speech-to-text model integrated into ClipScribe's production pipeline, providing uncensored transcription with superior cost efficiency compared to Gemini.

## Key Benefits

- **No Content Filters**: Transcribes all content without censorship
- **Superior Accuracy**: 1.8% WER vs Gemini's 2.3% WER
- **Cost Efficiency**: 70% lower cost than Gemini transcription
- **Production Ready**: Fully integrated into v2.51.0 pipeline

## Current Implementation

Voxtral is used as the primary transcription engine in the HybridProcessor, paired with Grok-4 for intelligence extraction.

## Models Available

## 📊 Models and Pricing

| Model | Parameters | Use Case | Price |
|-------|-----------|----------|-------|
| **Voxtral Small** | 24B | Production, highest accuracy | $0.001/min |
| **Voxtral Mini** | 3B | Edge deployment, balanced | $0.001/min |
| **Voxtral Mini Transcribe** | 3B | Optimized for transcription | $0.001/min |

**Note**: All models have the same API pricing!

## 🎯 Technical Limits

