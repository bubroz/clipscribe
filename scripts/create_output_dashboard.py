#!/usr/bin/env python3
"""
Output Dashboard Creator

Creates an HTML dashboard for browsing and downloading all processed video outputs.
This provides a user-friendly interface to access all the generated intelligence files.
"""

import os
import json
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class OutputDashboard:
    """Creates a web dashboard for output management and downloads."""

    def __init__(self, output_dir: str = "output", dashboard_dir: str = "output/dashboard"):
        self.output_dir = Path(output_dir)
        self.dashboard_dir = Path(dashboard_dir)
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)

    def scan_outputs(self) -> List[Dict[str, Any]]:
        """Scan all output directories and collect metadata."""
        videos = []

        # Scan both output/ and tests/output/ directories
        for base_dir in [self.output_dir, Path("tests/output")]:
            if not base_dir.exists():
                continue

            for video_dir in base_dir.iterdir():
                if not video_dir.is_dir() or not video_dir.name.startswith(("2025", "2024", "2023")):
                    continue

                manifest_path = video_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)

                        # Get file sizes
                        files_info = {}
                        total_size = 0
                        for file_key, file_data in manifest.get("files", {}).items():
                            file_path = video_dir / file_data["path"]
                            if file_path.exists():
                                size = file_path.stat().st_size
                                files_info[file_key] = {
                                    **file_data,
                                    "actual_size": size,
                                    "exists": True
                                }
                                total_size += size
                            else:
                                files_info[file_key] = {**file_data, "exists": False}

                        video_info = {
                            "id": video_dir.name,
                            "base_dir": str(base_dir),
                            "manifest": manifest,
                            "files": files_info,
                            "total_size": total_size,
                            "created_at": manifest.get("created_at", ""),
                            "entity_count": len(manifest.get("extraction_stats", {}).get("gemini_entities", [])),
                            "relationship_count": len(manifest.get("extraction_stats", {}).get("gemini_relationships", []))
                        }
                        videos.append(video_info)

                    except Exception as e:
                        print(f"Error reading {manifest_path}: {e}")
                        continue

        # Sort by creation date (newest first)
        videos.sort(key=lambda x: x["created_at"], reverse=True)
        return videos

    def create_zip_archive(self, video_info: Dict[str, Any]) -> str:
        """Create a ZIP archive of all files for a video."""
        video_dir = Path(video_info["base_dir"]) / video_info["id"]
        zip_path = self.dashboard_dir / f"{video_info['id']}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_info in video_info["files"].values():
                if file_info.get("exists", False):
                    file_path = video_dir / file_info["path"]
                    zipf.write(file_path, file_info["path"])

        return str(zip_path)

    def generate_html_dashboard(self, videos: List[Dict[str, Any]]) -> str:
        """Generate HTML dashboard with download links."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClipScribe Output Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            text-align: center;
        }}
        .stat-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }}
        .video-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            padding: 20px;
        }}
        .video-card {{
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .video-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .video-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #2c3e50;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .video-meta {{
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 15px;
        }}
        .download-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: #007bff;
            color: white;
        }}
        .btn-primary:hover {{
            background: #0056b3;
        }}
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        .btn-secondary:hover {{
            background: #545b62;
        }}
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        .btn-success:hover {{
            background: #1e7e34;
        }}
        .file-list {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e9ecef;
        }}
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px 0;
            font-size: 13px;
        }}
        .file-size {{
            color: #6c757d;
            font-size: 12px;
        }}
        .entity-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 10px;
        }}
        .entity-badge {{
            background: #e9ecef;
            color: #495057;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }}
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }}
        .search-box {{
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }}
        .search-input {{
            width: 100%;
            padding: 12px;
            border: 1px solid #ced4da;
            border-radius: 5px;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 ClipScribe Output Dashboard</h1>
            <p>Access and download your processed video intelligence</p>
        </div>

        <div class="stats">
            <div class="stat-box">
                <h3>{len(videos)}</h3>
                <p>Processed Videos</p>
            </div>
            <div class="stat-box">
                <h3>{sum(v['entity_count'] for v in videos)}</h3>
                <p>Total Entities</p>
            </div>
            <div class="stat-box">
                <h3>{sum(v['relationship_count'] for v in videos)}</h3>
                <p>Total Relationships</p>
            </div>
            <div class="stat-box">
                <h3>{sum(v['total_size'] for v in videos) // (1024*1024):.1f}MB</h3>
                <p>Total Output Size</p>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" class="search-input" placeholder="Search videos by title...">
        </div>

        <div class="video-grid" id="videoGrid">
"""

        if not videos:
            html += """
            <div class="empty-state">
                <h2>No Processed Videos Found</h2>
                <p>Process some videos with ClipScribe to see your intelligence outputs here.</p>
            </div>
            """

        for video in videos:
            manifest = video["manifest"]
            video_data = manifest.get("video", {})

            # Create ZIP archive for this video
            zip_path = self.create_zip_archive(video)

            # Get top entities for badges
            entities = manifest.get("extraction_stats", {}).get("gemini_entities", [])[:5]

            html += f"""
            <div class="video-card" data-title="{video_data.get('title', 'Unknown').lower()}">
                <div class="video-title">{video_data.get('title', 'Unknown Title')}</div>
                <div class="video-meta">
                    📅 {video['created_at'][:10] if video['created_at'] else 'Unknown date'}<br>
                    🎯 {video['entity_count']} entities, {video['relationship_count']} relationships<br>
                    💾 {video['total_size'] // 1024:.0f}KB total
                </div>

                <div class="entity-badges">
                    {"".join(f'<span class="entity-badge">{e["name"]}</span>' for e in entities)}
                </div>

                <div class="download-buttons">
                    <a href="{zip_path}" class="btn btn-primary" download>
                        📦 Download All Files
                    </a>
                    <a href="{video['base_dir']}/{video['id']}/report.md" class="btn btn-secondary" target="_blank">
                        📋 View Report
                    </a>
                    <a href="{video['base_dir']}/{video['id']}/knowledge_graph.json" class="btn btn-success" download>
                        🕸️ Knowledge Graph
                    </a>
                </div>

                <div class="file-list">
                    {chr(10).join(f'<div class="file-item"><span>{file_info["path"]}</span><span class="file-size">{file_info.get("actual_size", 0) // 1024}KB</span></div>' for file_info in video["files"].values() if file_info.get("exists", False))}
                </div>
            </div>
            """

        html += """
        </div>
    </div>

    <script>
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const videoGrid = document.getElementById('videoGrid');
        const videoCards = videoGrid.querySelectorAll('.video-card');

        searchInput.addEventListener('input', function() {{
            const searchTerm = this.value.toLowerCase();

            videoCards.forEach(card => {{
                const title = card.dataset.title;
                if (title.includes(searchTerm)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }});
    </script>
</body>
</html>
        """

        return html

    def create_dashboard(self) -> str:
        """Create the complete output dashboard."""
        print("🔍 Scanning output directories...")
        videos = self.scan_outputs()

        print(f"📊 Found {len(videos)} processed videos")

        print("🎨 Generating HTML dashboard...")
        html_content = self.generate_html_dashboard(videos)

        dashboard_path = self.dashboard_dir / "index.html"
        with open(dashboard_path, 'w') as f:
            f.write(html_content)

        print(f"✅ Dashboard created at: {dashboard_path}")
        print(f"🌐 Open in browser: file://{dashboard_path.absolute()}")

        return str(dashboard_path)


if __name__ == "__main__":
    dashboard = OutputDashboard()
    dashboard_path = dashboard.create_dashboard()
    print(f"\n🎉 Output Dashboard Ready!")
    print(f"📂 Location: {dashboard_path}")
    print(f"🔗 Open: file://{Path(dashboard_path).absolute()}")
