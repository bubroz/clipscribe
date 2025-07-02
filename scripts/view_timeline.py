#!/usr/bin/env python3
"""
Simple HTTP server to view TimelineJS timelines locally.

Usage:
    python scripts/view_timeline.py path/to/timeline/directory
"""

import http.server
import socketserver
import os
import sys
import webbrowser
from pathlib import Path

def serve_timeline(directory: str, port: int = 8000):
    """Serve a timeline directory with a simple HTTP server."""
    # Change to the timeline directory
    original_dir = os.getcwd()
    timeline_dir = Path(directory).resolve()
    
    if not timeline_dir.exists():
        print(f"Error: Directory '{timeline_dir}' does not exist")
        return
        
    if not (timeline_dir / "timeline_js.json").exists():
        print(f"Error: No timeline_js.json found in '{timeline_dir}'")
        return
        
    if not (timeline_dir / "view_timeline.html").exists():
        print(f"Error: No view_timeline.html found in '{timeline_dir}'")
        print("Creating one for you...")
        create_viewer_html(timeline_dir)
    
    os.chdir(timeline_dir)
    
    # Create the server
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"\n📊 ClipScribe Timeline Viewer")
            print(f"{'='*50}")
            print(f"Serving timeline from: {timeline_dir}")
            print(f"View at: http://localhost:{port}/view_timeline.html")
            print(f"{'='*50}")
            print(f"Press Ctrl+C to stop the server\n")
            
            # Open browser automatically
            webbrowser.open(f"http://localhost:{port}/view_timeline.html")
            
            # Start serving
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    finally:
        os.chdir(original_dir)

def create_viewer_html(directory: Path):
    """Create a basic viewer HTML if it doesn't exist."""
    viewer_content = '''<!DOCTYPE html>
<html>
<head>
    <title>ClipScribe Timeline</title>
    <link title="timeline-styles" rel="stylesheet" href="https://cdn.knightlab.com/libs/timeline3/latest/css/timeline.css">
    <script src="https://cdn.knightlab.com/libs/timeline3/latest/js/timeline.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #timeline-embed { width: 100%; height: 100vh; }
    </style>
</head>
<body>
    <div id="timeline-embed"></div>
    <script>
        fetch('timeline_js.json')
            .then(response => response.json())
            .then(data => {
                new TL.Timeline('timeline-embed', data);
            });
    </script>
</body>
</html>'''
    
    with open(directory / "view_timeline.html", "w") as f:
        f.write(viewer_content)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        # Default to the most recent timeline
        directory = "output/timeline_js_test_final/20250702_youtube_6ZVj1_SE4Mo"
    
    serve_timeline(directory) 