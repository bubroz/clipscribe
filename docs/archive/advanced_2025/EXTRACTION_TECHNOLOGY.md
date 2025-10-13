# ClipScribe Extraction Technology

*Last Updated: 2025-08-08*
*Version: v2.29.3*

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

## Extraction Philosophy: Quality-First & Hybrid (Gemini + Local Models)

Our architecture is built on a "Trust Gemini" principle for the primary extraction, complemented by a targeted hybrid layer using local models where they add value (SpaCy, GLiNER, REBEL) and LLM-based validation.

- **Primary Path (Gemini)**: Video/audio is processed by the selected Gemini model, which performs transcription and a comprehensive first-pass intelligence extraction in a single step.
- **Targeted Hybrid Augmentation**: We apply minimal, cost-aware local passes to improve recall, disambiguation, and validation when needed. This preserves speed while boosting completeness and consistency.
- **Focus on Prompts**: We continuously optimize Gemini prompts for completeness and correctness to minimize unnecessary post-processing.

We exclusively use the Gemini 2.5 generation (Flash and Pro). We do not use older models like 1.5.