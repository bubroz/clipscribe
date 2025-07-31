# ClipScribe Extraction Technology

*Last Updated: July 30, 2025*
*Version: v2.21.0*

## Core Extraction Engine: Google's Gemini 2.5

ClipScribe's intelligence extraction is a **cloud-native system** that leverages the best of Google's Gemini 2.5 model family to achieve a balance of quality, speed, and cost.

### Gemini 2.5 Pro (Default Model)
- **Primary Engine**: Used by default for all transcription, entity extraction, and relationship mapping.
- **Quality**: Provides state-of-the-art, professional-grade intelligence with high accuracy and semantic richness.
- **Use Case**: The recommended model for all analytical and research tasks where quality is paramount.

### Gemini 2.5 Flash (Optional Model)
- **High-Speed Option**: Available via the `--use-flash` flag for users who need to prioritize speed or cost.
- **Performance**: Approximately 15-30% faster than the Pro model.
- **Trade-off**: While still high quality, it may produce more "noise" and less refined relationships compared to the Pro model.
- **Use Case**: Ideal for high-volume batch processing or rapid initial analysis.

## Extraction Philosophy: Quality-First

Our architecture is built on a "Trust Gemini" principle. We have moved away from a complex, multi-stage pipeline involving local models (like GLiNER and REBEL) for the primary extraction path.

- **Simplified Pipeline**: Video/audio is sent directly to the selected Gemini model, which performs transcription and a comprehensive first-pass intelligence extraction in a single step.
- **No Redundancy**: We no longer re-process the transcript with multiple, redundant local models. This improves speed, reduces complexity, and ensures a single source of truth for the extracted data.
- **Focus on Prompts**: Our development effort is focused on optimizing the prompts sent to the Gemini models to continually improve the quality and richness of the data we get back.

We exclusively use the 2.5 generation of models to ensure we are always leveraging the latest technology. We do not use older models like 1.5.
