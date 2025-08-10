from clipscribe.retrievers.vertex_ai_transcriber import VertexAITranscriber


def test_strip_code_fences():
    # Avoid instantiating which triggers GCP clients by calling the unbound function
    wrapped = """```json
{
  "transcript": {"segments": [], "full_text": ""},
  "entities": [],
  "relationships": []
}
```"""
    out = VertexAITranscriber._strip_code_fences(None, wrapped)  # type: ignore
    assert out.strip().startswith("{") and out.strip().endswith("}")

