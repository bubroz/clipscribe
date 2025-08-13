from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever


def test_cache_key_is_sha256_based_and_stable():
    r = VideoIntelligenceRetriever(use_advanced_extraction=False)
    key1 = r._get_cache_key("https://Example.com/Path?b=2&a=1#frag")
    key2 = r._get_cache_key("https://example.com/Path?a=1&b=2")
    assert key1 == key2
    assert len(key1) == 24


