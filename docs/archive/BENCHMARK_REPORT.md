# Benchmark Plan: Hybrid vs. Pro-Only Extraction

*Last Updated: July 30, 2025*

This document outlines the plan and results for a comprehensive benchmark analysis comparing ClipScribe's default hybrid extraction model with the `--use-pro` (Gemini 2.5 Pro-only) model.

## 1. Objective

To empirically quantify the trade-offs between the two extraction models. The final report will provide a clear, data-driven recommendation for the default extraction strategy that best aligns with ClipScribe's goal of providing professional, intelligence-grade insights.

## 2. Test Data Selection

The following videos have been selected to provide a robust and representative sample of content types:

| # | Type | Title | URL | Rationale |
|---|---|---|---|---|
| 1 | Technical Training | How to Pass Tier 1 & 2 Selections Part 1/3 | `https://www.youtube.com/watch?v=Nr7vbOSzpSk` | Dense with specific terminology and concepts; a core competency test. |
| 2 | Investigative Journalism | Global Spyware Scandal: Exposing Pegasus Part One | `https://www.youtube.com/watch?v=6ZVj1_SE4Mo` | Tests extraction from a narrative format with complex relationships. |
| 3 | News Broadcast | PBS News Hour full episode, July 16, 2025 | `https://www.youtube.com/watch?v=0jeZPnNPp9M` | Multi-topic, multi-speaker format to test robustness. |

## 3. Methodology

1.  **Environment Preparation:** The `cache/` directory will be cleared before each run to ensure no cached results are used.
2.  **Execution:** Each video will be processed twice:
    - **Hybrid:** `poetry run clipscribe transcribe "URL" --output-dir "output/benchmark/hybrid/{video_id}" --performance-report`
    - **Pro-Only:** `poetry run clipscribe transcribe "URL" --output-dir "output/benchmark/pro/{video_id}" --performance-report --use-pro`

## 4. Data Collection & Metrics

- **Quantitative Metrics:**
  - Processing Time (s)
  - Processing Cost ($)
  - Entity Count
  - Relationship Count
- **Qualitative Analysis:**
  - Subjective review of entity and relationship quality.
  - Assessment of the overall coherence of the knowledge graph.

## 5. Benchmark Results (To Be Completed)

### Quantitative Results

| Video | Mode | Time (s) | Cost ($) | Entities | Relationships |
|---|---|---|---|---|---|
| **Tier 1 Selection** | Hybrid | 114.10 | $0.0167 | 36 | 71 |
| | Pro-Only | 133.29 | $0.0167 | 29 | 42 |
| **Pegasus Scandal** | Hybrid | 171.87 | $0.1826 | 69 | 98 |
| | Pro-Only | 255.54 | $0.1826 | 64 | 52 |
| **PBS News Hour** | Hybrid | 216.38 | $0.1946 | 101 | 113 |
| | Pro-Only | 420.58 | $0.1946 | 120 | 51 |

### Qualitative Analysis

**Video 1: Tier 1 Selection**

*   **Hybrid Model:** Cast a wide net, resulting in significant noise. It incorrectly identified generic roles ("Speaker") as distinct entities and created many low-value relationships with simplistic, literal predicates (`have_levels_like`). The output is comprehensive in quantity but requires significant manual cleanup.
*   **Pro-Only Model:** The output is far superior in quality. The entity list is clean, precise, and professionally relevant, avoiding the noise of the hybrid model. The relationships are semantically rich, using analytical predicates (`is_colloquially_known_as`, `has_organizational_structure_based_on`) that demonstrate a deeper understanding of the content. The output is immediately usable for professional analysis.
*   **Conclusion:** The Pro-Only model's output is overwhelmingly superior in quality and professional utility.

**Video 2: Pegasus Scandal**

*   **Hybrid Model:** Produced a higher quantity of entities and relationships, but with noticeable noise (e.g., generic entities like "Mobile phones"). Many relationships were simplistic and literal (`recabada_por`). The output is acceptable but requires manual filtering.
*   **Pro-Only Model:** Extracted slightly fewer entities but of higher relevance. The relationships were significantly better, using strong, analytical predicates (`initiated_investigation_with`, `provided_surveillance_instrument_to`) that captured the core narrative of the investigation. The resulting knowledge graph is cleaner and more impactful.
*   **Conclusion:** The Pro model demonstrates a better understanding of the journalistic narrative, producing a more coherent and analytically valuable output.

**Video 3: PBS News Hour**

*   **Hybrid Model:** Captured a massive volume of data, extracting more than double the relationships of the Pro model. However, the entities were noisier and the relationship predicates were less refined. This "shotgun" approach provided a vast amount of raw data that could be useful for deep-dive discovery, at the cost of requiring significant manual filtering.
*   **Pro-Only Model:** Acted more like an editor. It produced a cleaner and more accurate set of entities and events. The relationships were of higher semantic quality, focusing on the most critical connections. The output is a more focused "executive summary" of the broadcast but misses some of the secondary links captured by the hybrid model.
*   **Conclusion:** This highlights the core trade-off. The Pro model provides a cleaner, more accurate high-level summary, while the Hybrid model provides a larger, albeit noisier, dataset for raw intelligence gathering.

## 5. Final Recommendation

Based on the comprehensive quantitative and qualitative analysis, the evidence presents a clear trade-off:

*   **Pro-Only (`--use-pro`):** Consistently delivers a **higher quality** of intelligence. The outputs are cleaner, more accurate, and semantically richer. It acts like a skilled analyst, providing a refined, immediately usable knowledge graph. However, it is slower.
*   **Hybrid (Default):** Is significantly **faster** and often produces a **higher quantity** of raw data. However, this comes at the cost of significant noise and lower-quality outputs that require manual cleanup.

**Recommendation: Make `--use-pro` the default behavior and rename the flag to `--use-flash` to optionally select the faster, lower-quality model.**

**Justification:**

1.  **Aligns with Core Identity:** ClipScribe's mission is to provide high-quality, structured knowledge. The Pro model better aligns with this goal.
2.  **Prioritizes Quality:** For professional intelligence, accuracy is more important than raw quantity.
3.  **Better User Experience:** New users will experience the best the tool has to offer by default.
4.  **Preserves Flexibility:** Power users can still opt for the faster Flash model when speed is the priority.

