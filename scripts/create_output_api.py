#!/usr/bin/env python3
"""
Output API Server

Simple FastAPI server to provide programmatic access to processed video outputs.
Provides REST endpoints for listing, downloading, and managing output files.
"""

import os
import json
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


class VideoOutput(BaseModel):
    """Video output metadata model."""
    id: str
    title: str
    url: str
    created_at: str
    entity_count: int
    relationship_count: int
    total_size: int
    files: Dict[str, Any]


class OutputAPIServer:
    """FastAPI server for output management."""

    def __init__(self, output_dir: str = "output", port: int = 8081):
        self.output_dir = Path(output_dir)
        self.app = FastAPI(title="ClipScribe Output API", version="1.0.0")
        self.port = port
        self._setup_routes()

    def _scan_outputs(self) -> List[Dict[str, Any]]:
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

    def _create_zip_archive(self, video_info: Dict[str, Any]) -> str:
        """Create a ZIP archive of all files for a video."""
        video_dir = Path(video_info["base_dir"]) / video_info["id"]
        zip_path = self.output_dir / "dashboard" / f"{video_info['id']}.zip"

        # Ensure dashboard directory exists
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_info in video_info["files"].values():
                if file_info.get("exists", False):
                    file_path = video_dir / file_info["path"]
                    zipf.write(file_path, file_info["path"])

        return str(zip_path)

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/")
        async def root():
            """API root endpoint."""
            return {
                "name": "ClipScribe Output API",
                "version": "1.0.0",
                "description": "REST API for accessing processed video intelligence outputs",
                "endpoints": {
                    "/videos": "List all processed videos",
                    "/videos/{video_id}": "Get specific video details",
                    "/videos/{video_id}/download": "Download all files as ZIP",
                    "/videos/{video_id}/files/{filename}": "Download individual file",
                    "/dashboard": "Open HTML dashboard in browser"
                }
            }

        @self.app.get("/videos", response_model=List[VideoOutput])
        async def list_videos(
            limit: int = Query(50, description="Maximum number of videos to return"),
            offset: int = Query(0, description="Number of videos to skip"),
            search: Optional[str] = Query(None, description="Search videos by title")
        ):
            """List all processed videos with optional filtering."""
            videos = self._scan_outputs()

            # Apply search filter
            if search:
                search_lower = search.lower()
                videos = [
                    v for v in videos
                    if search_lower in v["manifest"].get("video", {}).get("title", "").lower()
                ]

            # Apply pagination
            videos = videos[offset:offset + limit]

            # Format response
            response = []
            for video in videos:
                manifest = video["manifest"]
                video_data = manifest.get("video", {})

                response.append(VideoOutput(
                    id=video["id"],
                    title=video_data.get("title", "Unknown Title"),
                    url=video_data.get("url", ""),
                    created_at=video["created_at"],
                    entity_count=video["entity_count"],
                    relationship_count=video["relationship_count"],
                    total_size=video["total_size"],
                    files=video["files"]
                ))

            return response

        @self.app.get("/videos/{video_id}")
        async def get_video(video_id: str):
            """Get detailed information about a specific video."""
            videos = self._scan_outputs()
            video = next((v for v in videos if v["id"] == video_id), None)

            if not video:
                raise HTTPException(status_code=404, detail="Video not found")

            return video

        @self.app.get("/videos/{video_id}/download")
        async def download_video_zip(video_id: str):
            """Download all files for a video as a ZIP archive."""
            videos = self._scan_outputs()
            video = next((v for v in videos if v["id"] == video_id), None)

            if not video:
                raise HTTPException(status_code=404, detail="Video not found")

            zip_path = self._create_zip_archive(video)

            if not Path(zip_path).exists():
                raise HTTPException(status_code=500, detail="Failed to create ZIP archive")

            return FileResponse(
                path=zip_path,
                filename=f"{video_id}.zip",
                media_type="application/zip"
            )

        @self.app.get("/videos/{video_id}/files/{filename}")
        async def download_file(video_id: str, filename: str):
            """Download a specific file from a video's output."""
            videos = self._scan_outputs()
            video = next((v for v in videos if v["id"] == video_id), None)

            if not video:
                raise HTTPException(status_code=404, detail="Video not found")

            file_path = Path(video["base_dir"]) / video_id / filename

            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")

            # Determine content type based on file extension
            content_types = {
                ".json": "application/json",
                ".txt": "text/plain",
                ".md": "text/markdown",
                ".csv": "text/csv",
                ".zip": "application/zip"
            }
            content_type = content_types.get(file_path.suffix, "application/octet-stream")

            return FileResponse(
                path=str(file_path),
                filename=filename,
                media_type=content_type
            )

        @self.app.get("/dashboard")
        async def open_dashboard():
            """Redirect to HTML dashboard."""
            dashboard_path = self.output_dir / "dashboard" / "index.html"
            if dashboard_path.exists():
                return FileResponse(
                    path=str(dashboard_path),
                    media_type="text/html"
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Dashboard not found. Run 'clipscribe dashboard' to create it."
                )

        @self.app.get("/stats")
        async def get_stats():
            """Get overall statistics about processed videos."""
            videos = self._scan_outputs()

            total_videos = len(videos)
            total_entities = sum(v["entity_count"] for v in videos)
            total_relationships = sum(v["relationship_count"] for v in videos)
            total_size = sum(v["total_size"] for v in videos)

            # File type breakdown
            file_types = {}
            for video in videos:
                for file_info in video["files"].values():
                    if file_info.get("exists", False):
                        ext = Path(file_info["path"]).suffix
                        file_types[ext] = file_types.get(ext, 0) + 1

            return {
                "total_videos": total_videos,
                "total_entities": total_entities,
                "total_relationships": total_relationships,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_type_breakdown": file_types,
                "videos_by_platform": {},
                "last_updated": datetime.now().isoformat()
            }

    def run(self):
        """Run the API server."""
        print(f"🚀 Starting ClipScribe Output API Server")
        print(f"📡 Server: http://localhost:{self.port}")
        print(f"📊 Dashboard: http://localhost:{self.port}/dashboard")
        print(f"📋 API Docs: http://localhost:{self.port}/docs")
        print("")
        print("Available endpoints:")
        print(f"• GET /videos - List all processed videos")
        print(f"• GET /videos/{{video_id}} - Get video details")
        print(f"• GET /videos/{{video_id}}/download - Download ZIP archive")
        print(f"• GET /videos/{{video_id}}/files/{{filename}} - Download individual file")
        print(f"• GET /stats - Get overall statistics")
        print("")
        print("Press Ctrl+C to stop the server")

        uvicorn.run(self.app, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    server = OutputAPIServer()
    server.run()
