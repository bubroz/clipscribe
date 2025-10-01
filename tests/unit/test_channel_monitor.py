"""Tests for channel monitor."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.clipscribe.monitors.channel_monitor import ChannelMonitor


@pytest.fixture
def mock_feed():
    """Mock feedparser response with proper .get() behavior."""
    # Create mock entries with proper dict-like get()
    entry1 = MagicMock()
    entry1.get.side_effect = lambda k, d=None: {
        'yt_videoid': 'abc123',
        'link': 'https://youtube.com/watch?v=abc123',
        'title': 'Test Video 1',
        'published': '2025-09-30T12:00:00+00:00'
    }.get(k, d)
    entry1.yt_videoid = 'abc123'
    
    entry2 = MagicMock()
    entry2.get.side_effect = lambda k, d=None: {
        'yt_videoid': 'def456',
        'link': 'https://youtube.com/watch?v=def456',
        'title': 'Test Video 2',
        'published': '2025-09-30T13:00:00+00:00'
    }.get(k, d)
    entry2.yt_videoid = 'def456'
    
    feed_mock = MagicMock()
    feed_mock.entries = [entry1, entry2]
    feed_mock.feed.get.side_effect = lambda k, d=None: {'title': 'Test Channel'}.get(k, d)
    
    return feed_mock


def test_channel_monitor_initialization(tmp_path):
    """Test monitor initializes correctly."""
    state_file = tmp_path / "state.json"
    monitor = ChannelMonitor(['UC123'], state_file=state_file)
    
    assert len(monitor.channel_ids) == 1
    assert monitor.channel_ids[0] == 'UC123'
    assert len(monitor.seen_videos) == 0


def test_get_rss_url():
    """Test RSS URL generation."""
    monitor = ChannelMonitor(['UC123'])
    url = monitor.get_rss_url('UC123')
    
    assert url == 'https://www.youtube.com/feeds/videos.xml?channel_id=UC123'


def test_get_channel_id_from_url(tmp_path):
    """Test channel ID extraction from URLs."""
    monitor = ChannelMonitor([], state_file=tmp_path / "state.json")
    
    # Channel ID URL
    assert monitor.get_channel_id_from_url('https://youtube.com/channel/UCabc123/videos') == 'UCabc123'
    
    # Direct ID (24 chars starting with UC)
    valid_id = 'UCabc123def4567890123456'  # Exactly 24 chars
    assert len(valid_id) == 24
    assert monitor.get_channel_id_from_url(valid_id) == valid_id
    
    # Invalid URL (@username not supported yet)
    assert monitor.get_channel_id_from_url('https://youtube.com/@username') is None


@pytest.mark.asyncio
async def test_check_channel_finds_new_videos(tmp_path, mock_feed):
    """Test that new videos are detected."""
    state_file = tmp_path / "state.json"
    monitor = ChannelMonitor(['UC123'], state_file=state_file)
    
    with patch('feedparser.parse', return_value=mock_feed):
        new_videos = await monitor._check_channel('UC123')
    
    assert len(new_videos) == 2
    assert new_videos[0]['video_id'] == 'abc123'
    assert new_videos[0]['title'] == 'Test Video 1'
    assert new_videos[1]['video_id'] == 'def456'


@pytest.mark.asyncio
async def test_duplicate_detection(tmp_path, mock_feed):
    """Test that duplicate videos are not returned."""
    state_file = tmp_path / "state.json"
    monitor = ChannelMonitor(['UC123'], state_file=state_file)
    
    with patch('feedparser.parse', return_value=mock_feed):
        # First check - should find 2 new videos
        new_videos_1 = await monitor._check_channel('UC123')
        assert len(new_videos_1) == 2
        
        # Second check - should find 0 (already seen)
        new_videos_2 = await monitor._check_channel('UC123')
        assert len(new_videos_2) == 0


@pytest.mark.asyncio
async def test_state_persistence(tmp_path, mock_feed):
    """Test that seen videos persist across restarts."""
    state_file = tmp_path / "state.json"
    
    # First monitor instance
    monitor1 = ChannelMonitor(['UC123'], state_file=state_file)
    
    with patch('feedparser.parse', return_value=mock_feed):
        await monitor1.check_for_new_videos()
    
    assert len(monitor1.seen_videos) == 2
    assert state_file.exists()
    
    # Second monitor instance (simulates restart)
    monitor2 = ChannelMonitor(['UC123'], state_file=state_file)
    
    # Should load previously seen videos
    assert len(monitor2.seen_videos) == 2
    assert 'abc123' in monitor2.seen_videos
    assert 'def456' in monitor2.seen_videos


@pytest.mark.asyncio
async def test_check_for_new_videos_multiple_channels(tmp_path, mock_feed):
    """Test checking multiple channels."""
    state_file = tmp_path / "state.json"
    monitor = ChannelMonitor(['UC123', 'UC456'], state_file=state_file)
    
    with patch('feedparser.parse', return_value=mock_feed):
        new_videos = await monitor.check_for_new_videos()
    
    # Should find videos from first channel (mock returns same feed for both)
    assert len(new_videos) >= 2  # At least 2 videos detected

