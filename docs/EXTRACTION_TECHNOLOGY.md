# Extraction Technology in ClipScribe

This document explains the advanced extraction technologies, `GLiNER` and `REBEL`, that power ClipScribe's video intelligence features.

## Why GLiNER + REBEL is Powerful

ClipScribe uses a sophisticated hybrid model to build rich, queryable knowledge graphs from video content. This is achieved by combining two cutting-edge models:

### GLiNER: The Universal Entity Finder

GLiNER finds the **NODES** (entities) of our knowledge graph. Unlike traditional Named Entity Recognition (NER) systems that are limited to a fixed set of categories (like PERSON, ORGANIZATION), GLiNER is a universal entity finder.

-   **Flexible**: It can find *any* entity type you describe with natural language, not just from a predefined list.
-   **Context-Aware**: It understands the difference between "Apple" (the company) and "apple" (the fruit) based on the surrounding text.
-   **Zero-Shot**: It doesn't require any special training to find entities in new, specialized domains.

**Example: Dynamic Entity Detection**

If we are analyzing a cooking video, we can ask GLiNER to find culinary-specific entities like `chef`, `dish`, `ingredient`, and `cooking_technique`. For a tech tutorial, we can ask for `programming_framework`, `database`, and `cloud_service`. GLiNER handles this dynamically without any code changes.

### REBEL: The Relationship Extractor

REBEL finds the **EDGES** (relationships) that connect the entities GLiNER discovers. It reads sentences and extracts semantic fact triples in the format `(Subject) -> [Predicate] -> (Object)`.

-   **Semantic**: It understands the meaning behind the words to find relationships like `founded`, `located in`, `works for`, or `competes with`.
-   **Directional**: It correctly identifies the subject and object in a relationship (e.g., `SpaceX manufactures Falcon 9`, not the other way around).
-   **Contextual**: It can extract implied relationships from the text.

**Example: Extracting Knowledge Graph Triples**

From the text: *"Elon Musk founded SpaceX in 2002. The company is headquartered in Hawthorne, California."*

REBEL extracts triples like:
-   `(Elon Musk) -> [founded] -> (SpaceX)`
-   `(SpaceX) -> [inception] -> (2002)`
-   `(SpaceX) -> [headquarters location] -> (Hawthorne)`

## The Combined Power: Building Knowledge Graphs

Together, GLiNER and REBEL allow ClipScribe to transform unstructured video transcripts into highly structured knowledge graphs.

1.  **GLiNER** identifies all the relevant entities (the nodes).
2.  **REBEL** identifies how they are all connected (the edges).
3.  The result is a rich, queryable network of facts and information that allows for deep analysis and insights far beyond a simple transcript. 