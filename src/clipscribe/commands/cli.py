"""ClipScribe CLI - AI-powered video transcription and analysis tool.

This module provides the command-line interface for ClipScribe, supporting
transcription of videos from 1800+ platforms using the Voxtral-Grok pipeline
for uncensored intelligence extraction.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click

from ..config.logging_config import setup_logging
from ..config.settings import Settings
from ..extractors.multi_video_processor import MultiVideoProcessor
from ..models import VideoCollectionType
from ..version import __version__


@click.group()
@click.version_option(version=__version__, prog_name="ClipScribe")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    """ClipScribe - AI-powered video transcription and analysis."""
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level)

    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug


@cli.command("process")
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--transcription-provider", "-t",
    type=click.Choice(["voxtral", "whisperx-modal", "whisperx-local"]),
    default="whisperx-local",
    help="Transcription provider (voxtral=cheap/no-speakers, whisperx-modal=GPU/speakers, whisperx-local=M3-Max/free/speakers)"
)
@click.option(
    "--intelligence-provider", "-i",
    type=click.Choice(["grok"]),
    default="grok",
    help="Intelligence extraction provider"
)
@click.option(
    "--diarize/--no-diarize",
    default=True,
    help="Enable speaker diarization (if supported by provider)"
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(path_type=Path),
    default=Path("output"),
    help="Output directory"
)
@click.pass_context
def process(
    ctx: click.Context,
    audio_file: Path,
    transcription_provider: str,
    intelligence_provider: str,
    diarize: bool,
    output_dir: Path,
):
    """Process audio/video file to extract intelligence.
    
    v3.0.0 file-first processing with provider selection.
    
    Examples:
    
        Single-speaker content (cheap, no diarization):
        $ clipscribe process lecture.mp3 -t voxtral --no-diarize
        
        Multi-speaker, cloud GPU (quality):
        $ clipscribe process interview.mp3 -t whisperx-modal
        
        Multi-speaker, local M3 Max (FREE):
        $ clipscribe process podcast.mp3 -t whisperx-local
        
    Provider Comparison (30min video):
        voxtral:        ~$0.03  (API, no speakers)
        whisperx-modal: ~$0.06  (Cloud GPU, speakers)
        whisperx-local: $0.00   (M3 Max, FREE, speakers)
        
        Plus Grok intelligence: ~$0.005 per video
    """
    asyncio.run(process_file_logic(
        audio_file,
        transcription_provider,
        intelligence_provider,
        diarize,
        output_dir,
    ))


async def process_file_logic(
    audio_file: Path,
    transcription_provider: str,
    intelligence_provider: str,
    diarize: bool,
    output_dir: Path,
):
    """Core file processing logic using provider abstraction."""
    from clipscribe.providers.factory import (
        get_transcription_provider,
        get_intelligence_provider
    )
    from clipscribe.retrievers.output_formatter import OutputFormatter
    
    logger = logging.getLogger(__name__)
    
    # Initialize providers
    try:
        transcriber = get_transcription_provider(transcription_provider)
        extractor = get_intelligence_provider(intelligence_provider)
    except Exception as e:
        logger.error(f"Provider initialization failed: {e}")
        raise click.ClickException(str(e))
    
    # Validate diarization support
    if diarize and not transcriber.supports_diarization:
        logger.warning(
            f"{transcription_provider} does not support speaker diarization. "
            f"Processing without speakers. "
            f"Use -t whisperx-modal or -t whisperx-local for multi-speaker content."
        )
        diarize = False
    
    # Estimate costs (get duration)
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)],
            capture_output=True, text=True, timeout=10
        )
        duration = float(result.stdout.strip())
    except Exception:
        duration = 1800.0  # Default 30 min if can't detect
    transcript_cost_est = transcriber.estimate_cost(duration)
    transcript_length_est = int(duration * 150)  # Rough: 150 chars/sec
    intelligence_cost_est = extractor.estimate_cost(transcript_length_est)
    total_est = transcript_cost_est + intelligence_cost_est
    
    logger.info(f"\nFile: {audio_file.name}")
    logger.info(f"Duration: {duration/60:.1f} minutes")
    logger.info(f"Estimated cost: ${total_est:.4f}")
    logger.info(f"  Transcription ({transcription_provider}): ${transcript_cost_est:.4f}")
    logger.info(f"  Intelligence ({intelligence_provider}): ${intelligence_cost_est:.4f}")
    
    # Transcribe
    logger.info(f"\nTranscribing with {transcription_provider}...")
    transcript = await transcriber.transcribe(str(audio_file), diarize=diarize)
    logger.info(f"✓ Transcribed: {transcript.language}, {transcript.speakers} speakers")
    logger.info(f"  Actual cost: ${transcript.cost:.4f}")
    
    # Extract intelligence
    logger.info(f"\nExtracting intelligence with {intelligence_provider}...")
    intelligence = await extractor.extract(transcript, metadata={"filename": audio_file.name})
    logger.info(f"✓ Extracted: {len(intelligence.entities)} entities, {len(intelligence.relationships)} relationships")
    logger.info(f"  Actual cost: ${intelligence.cost:.4f}")
    
    # Display cache stats if available
    if intelligence.cache_stats.get("cached_tokens", 0) > 0:
        savings = intelligence.cache_stats.get("cache_savings", 0)
        logger.info(f"  💰 Cache savings: ${savings:.4f}")
    
    # Save outputs
    total_cost = transcript.cost + intelligence.cost
    logger.info(f"\nTotal cost: ${total_cost:.4f} (estimate was ${total_est:.4f})")
    
    # Create output directory
    import json
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{timestamp}_{audio_file.stem}"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save comprehensive JSON (v3.0.0 format - matches Modal)
    comprehensive_data = {
        "transcript": {
            "segments": [seg.dict() for seg in transcript.segments],
            "language": transcript.language,
            "duration": transcript.duration,
            "speakers": transcript.speakers,
            "provider": transcript.provider,
            "model": transcript.model,
            "cost": transcript.cost,
            "metadata": transcript.metadata,
        },
        "intelligence": {
            "entities": intelligence.entities,
            "relationships": intelligence.relationships,
            "topics": intelligence.topics,
            "key_moments": intelligence.key_moments,
            "sentiment": intelligence.sentiment,
            "provider": intelligence.provider,
            "model": intelligence.model,
            "cost": intelligence.cost,
            "cost_breakdown": intelligence.cost_breakdown,
            "cache_stats": intelligence.cache_stats,
        },
        "file_metadata": {
            "filename": audio_file.name,
            "processed_at": timestamp,
            "total_cost": total_cost,
            "transcription_cost": transcript.cost,
            "intelligence_cost": intelligence.cost,
        }
    }
    
    with open(output_path / "transcript.json", "w") as f:
        json.dump(comprehensive_data, f, indent=2)
    
    logger.info(f"\n✓ Complete! Results saved to {output_path}")
    logger.info(f"  Comprehensive JSON: {output_path}/transcript.json")
    logger.info(f"  Entities: {len(intelligence.entities)}")
    logger.info(f"  Relationships: {len(intelligence.relationships)}")
    logger.info(f"  Topics: {len(intelligence.topics)}")


def run_cli():
    """Run the CLI application."""
    cli()


if __name__ == "__main__":
    run_cli()




# === Utility Commands ===


@cli.group()
def utils():
    """Utility commands."""


@utils.command("clean-demo")
@click.option("--demo-dir", type=click.Path(path_type=Path), default=Path("output"))
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--keep-recent", type=int, default=0, help="Keep N most recent demo folders")
def clean_demo(demo_dir: Path, dry_run: bool, keep_recent: int):
    """Clean up old demo/test output folders."""
    if not demo_dir.exists():
        click.echo("Nothing to clean.")
        return

    # Identify candidate subdirectories
    subdirs = sorted(
        [p for p in demo_dir.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True
    )
    to_delete = subdirs[keep_recent:] if keep_recent > 0 else subdirs

    if dry_run:
        for d in to_delete:
            click.echo(f"Would delete: {d}")
        return

    for d in to_delete:
        try:
            import shutil

            shutil.rmtree(d)
            click.echo(f"Deleted: {d}")
        except Exception as e:
            click.echo(f"Failed to delete {d}: {e}")

    click.echo("Demo cleanup complete.")


@utils.command("check-auth")
def check_auth():
    """Report active authentication method and configuration."""
    try:
        settings = Settings()
    except Exception as e:
        click.echo("Auth status: Misconfigured")
        click.echo(f"Error: {e}")
        click.echo(
            "Configure MISTRAL_API_KEY for Voxtral transcription and XAI_API_KEY for Grok-4 intelligence extraction."
        )
        return

    use_vertex = getattr(settings, "use_vertex_ai", False)
    if use_vertex:
        project = (
            getattr(settings, "VERTEX_AI_PROJECT", None)
            or os.environ.get("VERTEX_AI_PROJECT")
            or os.environ.get("VERTEX_AI_PROJECT_ID")
        )
        location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        click.echo("Auth: Vertex AI mode enabled")
        click.echo(f"Project: {project or 'not set'}")
        click.echo(f"Location: {location}")
        if creds_path:
            exists = Path(creds_path).exists()
            click.echo(
                f"GOOGLE_APPLICATION_CREDENTIALS: {creds_path} ({'exists' if exists else 'missing'})"
            )
        else:
            click.echo("GOOGLE_APPLICATION_CREDENTIALS: not set (ADC will be used if available)")
        click.echo(
            "Verify quotas in Google Cloud Console > Vertex AI. Ensure service account has roles/aiplatform.user."
        )
    else:
        # Check Voxtral API key
        mistral_key = os.environ.get("MISTRAL_API_KEY", "")
        if mistral_key:
            masked = mistral_key[:6] + "..." if len(mistral_key) > 6 else "(set)"
            click.echo("Auth: Mistral API key detected")
            click.echo(f"MISTRAL_API_KEY: {masked}")
        else:
            click.echo("Auth: Missing MISTRAL_API_KEY")
            click.echo("Set MISTRAL_API_KEY for Voxtral transcription.")

        # Check xAI API key
        xai_key = os.environ.get("XAI_API_KEY", "")
        if xai_key:
            masked = xai_key[:6] + "..." if len(xai_key) > 6 else "(set)"
            click.echo("Auth: xAI API key detected")
            click.echo(f"XAI_API_KEY: {masked}")
        else:
            click.echo("Auth: Missing XAI_API_KEY")
            click.echo("Set XAI_API_KEY for Grok-4 intelligence extraction.")


@cli.command()
@click.option("--output-dir", default="output", help="Output directory to scan")
@click.option("--dashboard-dir", default="output/dashboard", help="Dashboard output directory")
def dashboard(output_dir, dashboard_dir):
    """Create an output dashboard for browsing and downloading processed videos.

    This command scans all processed video outputs and creates:
    • HTML dashboard with search and filtering
    • ZIP archives for easy downloading
    • Links to individual files and reports
    • Statistics and metadata overview
    """
    try:
        from scripts.create_output_dashboard import OutputDashboard
    except ImportError:
        click.echo("❌ Error: Output dashboard script not found.")
        click.echo("Run: python scripts/create_output_dashboard.py")
        return

    click.echo("🎥 Creating ClipScribe Output Dashboard...")

    dashboard_creator = OutputDashboard(output_dir=output_dir, dashboard_dir=dashboard_dir)
    dashboard_path = dashboard_creator.create_dashboard()

    click.echo("\n✅ Dashboard created successfully!")
    click.echo(f"📂 Location: {dashboard_path}")
    click.echo(f"🌐 Open in browser: file://{Path(dashboard_path).absolute()}")
    click.echo("")
    click.echo("📊 Features:")
    click.echo("• Browse all processed videos with search")
    click.echo("• Download individual files or complete ZIP archives")
    click.echo("• View entity and relationship counts")
    click.echo("• Access knowledge graphs, transcripts, and reports")
    click.echo("• File size information and download statistics")


@cli.command()
@click.argument("files_list", type=click.Path(exists=True))
@click.option(
    "--output-dir", "-o", default="output/batch", help="Output directory for batch results"
)
@click.option("--max-concurrent", "-c", type=int, default=3, help="Maximum concurrent jobs")
@click.option(
    "--transcription-provider", "-t",
    type=click.Choice(["voxtral", "whisperx-modal", "whisperx-local"]),
    default="whisperx-local",
    help="Transcription provider"
)
@click.option("--batch-id", help="Custom batch identifier (auto-generated if not provided)")
def batch_process(files_list, output_dir, max_concurrent, transcription_provider, batch_id):
    """Process multiple audio/video files in parallel (v3.0.0 file-based).

    FILES_LIST should contain one file path per line.

    Examples:
        clipscribe batch-process files.txt
        clipscribe batch-process files.txt --max-concurrent 5 -t whisperx-modal
    """
    click.echo("⚠️  Batch processing being updated for v3.0.0 provider architecture.")
    click.echo("Use individual 'clipscribe process' commands for now.")
    click.echo("Batch processing will be re-enabled in v3.1.0 with file support.")


@cli.command()
@click.argument("batch_id")
def batch_status(batch_id):
    """Check batch processing status (temporarily disabled in v3.0.0)."""
    click.echo("⚠️  Batch status checking temporarily disabled during v3.0.0 refactor.")
    click.echo("Will be re-enabled in v3.1.0 with file-based batch processing.")


@cli.command()
@click.argument("batch_id")
def batch_results(batch_id):
    """Get batch processing results (temporarily disabled in v3.0.0)."""
    click.echo("⚠️  Batch results temporarily disabled during v3.0.0 refactor.")
    click.echo("Will be re-enabled in v3.1.0 with file-based batch processing.")


@cli.command()
@click.argument("batch_id")
@click.option("--output-dir", "-o", default="output/batch", help="Batch output directory")
@click.option(
    "--cross-video/--single-video", default=True, help="Enable cross-video entity normalization"
)
def normalize_batch_entities(batch_id, output_dir, cross_video):
    """Normalize entities across all videos in a batch with cross-video linking.

    PHASE 2: This command analyzes entities from all videos in a batch and:
    - Performs cross-video entity deduplication
    - Links related entities across videos
    - Boosts confidence for entities appearing in multiple videos
    - Generates entity relationship networks

    Examples:
        clipscribe normalize-batch-entities batch_123abc
        clipscribe normalize-batch-entities batch_123abc --cross-video
        clipscribe normalize-batch-entities batch_123abc --single-video
    """

    async def _run():
        try:
            import json
            from pathlib import Path

            from ..extractors.entity_normalizer import EntityNormalizer

            batch_dir = Path(output_dir) / batch_id
            if not batch_dir.exists():
                click.echo(f"❌ Batch {batch_id} not found in {output_dir}", err=True)
                raise click.Abort()

            click.echo(f"🔍 Analyzing batch: {batch_id}")
            click.echo(f"📁 Location: {batch_dir}")
            click.echo(
                f"🔗 Cross-video normalization: {'✅ Enabled' if cross_video else '❌ Disabled'}"
            )

            # Collect entities from all video results in the batch
            video_entities = {}

            # Look for job result files
            job_dirs = [
                d
                for d in batch_dir.iterdir()
                if d.is_dir() and d.name.startswith(f"{batch_id}_job_")
            ]

            if not job_dirs:
                click.echo("❌ No job results found in batch", err=True)
                raise click.Abort()

            click.echo(f"📊 Found {len(job_dirs)} job results")

            # Load entities from each job
            for job_dir in job_dirs:
                results_file = job_dir / "results.json"
                if results_file.exists():
                    try:
                        with open(results_file, "r") as f:
                            job_results = json.load(f)

                        # Extract entities from job results
                        entities = []
                        if "entities" in job_results:
                            for entity_data in job_results["entities"]:
                                # Convert dict to Entity-like object
                                entity = type("Entity", (), entity_data)()
                                entities.append(entity)

                        if entities:
                            video_entities[job_dir.name] = entities
                            click.echo(f"  ✅ {job_dir.name}: {len(entities)} entities")

                    except Exception as e:
                        click.echo(f"  ⚠️  {job_dir.name}: Failed to load ({e})")
                        continue

            if not video_entities:
                click.echo("❌ No entities found in batch results", err=True)
                raise click.Abort()

            # Initialize normalizer
            normalizer = EntityNormalizer()

            if cross_video:
                # PHASE 2: Cross-video normalization
                click.echo("\\n🚀 PHASE 2: Starting cross-video entity normalization...")
                with click.progressbar(
                    length=len(video_entities), label="Processing videos"
                ) as bar:
                    result = normalizer.normalize_entities_across_videos(video_entities)
                    bar.update(len(video_entities))

                # Save comprehensive results
                output_file = batch_dir / "cross_video_normalization_results.json"
                with open(output_file, "w") as f:
                    json.dump(result, f, indent=2, default=str)

                # Display results
                stats = result["statistics"]
                click.echo("\\n🎉 Cross-video normalization complete!")
                click.echo("📊 Statistics:")
                click.echo(f"  Videos processed: {stats['input_videos']}")
                click.echo(f"  Total entities: {stats['total_input_entities']}")
                click.echo(f"  Normalized entities: {stats['cross_video_normalized_entities']}")
                click.echo(f"  Cross-video entities: {stats.get('multi_video_entities', 0)}")
                click.echo(f"  Deduplication ratio: {stats.get('deduplication_ratio', 0):.2f}")

                # Show top cross-video entities
                if result["insights"]["cross_video_entities"]:
                    click.echo("\\n🏆 Top Cross-Video Entities:")
                    for entity in result["insights"]["cross_video_entities"][:5]:
                        click.echo(
                            f"  • {entity['entity']} ({entity['type']}) - {len(entity['videos'])} videos"
                        )

                # Show video similarity
                if result["insights"]["video_similarity_scores"]:
                    click.echo("\\n🔗 Video Similarity Scores:")
                    for video_pair, similarity in list(
                        result["insights"]["video_similarity_scores"].items()
                    )[:3]:
                        click.echo(f"  • {video_pair}: {similarity:.2f}")

            else:
                # Single-video normalization only
                click.echo("\\n🔧 Performing single-video entity normalization...")
                single_results = {}

                for video_id, entities in video_entities.items():
                    normalized = normalizer.normalize_entities(entities)
                    single_results[video_id] = {
                        "original_count": len(entities),
                        "normalized_count": len(normalized),
                        "entities": [
                            {
                                "name": e.entity,
                                "type": e.type,
                                "confidence": getattr(e, "confidence", 0.5),
                            }
                            for e in normalized
                        ],
                    }

                # Save single-video results
                output_file = batch_dir / "single_video_normalization_results.json"
                with open(output_file, "w") as f:
                    json.dump(single_results, f, indent=2)

                total_normalized = sum(r["normalized_count"] for r in single_results.values())
                click.echo(f"✅ Single-video normalization complete: {total_normalized} entities")

            # Save summary
            summary_file = batch_dir / "entity_normalization_summary.txt"
            with open(summary_file, "w") as f:
                f.write("Entity Normalization Summary\\n")
                f.write(f"Batch ID: {batch_id}\\n")
                f.write(f"Cross-video enabled: {cross_video}\\n")
                f.write(
                    f"Timestamp: {json.dumps({'timestamp': str(datetime.now())}, default=str)}\\n"
                )

            click.echo("\\n💾 Results saved to:")
            click.echo(f"  📄 {output_file}")
            click.echo(f"  📋 {summary_file}")

            if cross_video:
                click.echo("\\n📈 Next steps:")
                click.echo(f"  • View detailed results: cat {output_file}")
                click.echo("  • Analyze entity networks: explore cross_video_links")
                click.echo("  • Check insights: review entity importance ranking")

        except Exception as e:
            click.echo(f"❌ Entity normalization failed: {e}", err=True)
            import traceback

            traceback.print_exc()
            raise click.Abort()

    asyncio.run(_run())


@cli.command("stats")
def show_stats():
    """Show processing statistics."""
    from ..utils.processing_tracker import ProcessingTracker

    tracker = ProcessingTracker()
    stats = tracker.get_stats()

    click.echo("\n📊 Processing Statistics\n")
    click.echo(f"Total: {stats['total_tracked']}")
    click.echo(f"  ✅ Completed: {stats['completed']}")
    click.echo(f"  ❌ Failed: {stats['failed']}")
    click.echo(f"Success rate: {stats['success_rate']}")


