"""
Station10 Intelligence Bot - Multi-user Telegram interface with webhook support.

Commands:
- /start - Register as Station10 user
- /process <URL> - Process video from URL
- /recent [N] - Last N videos
- /search <query> - Search entities
- /stats - Your usage and costs
- /help - Show help

Features:
- Direct video/document uploads (≤1.5GB via Telegram)
- Large file uploads (>1.5GB via signed R2 URL)
- Non-blocking async processing
- Webhook with secret token verification
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Optional
import tempfile

from aiohttp import web
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from ..database.db_manager import Station10Database
from ..retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2

logger = logging.getLogger(__name__)


class Station10Bot:
    """Multi-user Telegram bot for Station10 Media with webhook support."""

    def __init__(self):
        """Initialize Station10 bot."""
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.secret_token = os.getenv("TELEGRAM_SECRET_TOKEN")
        self.webhook_url = os.getenv("WEBHOOK_URL", "")
        self.port = int(os.getenv("PORT", 8080))

        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable required")
        if not self.secret_token:
            raise ValueError("TELEGRAM_SECRET_TOKEN environment variable required")

        self.db = Station10Database()
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "/home/station10/clipscribe/output/station10"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # File size threshold (1.5GB)
        self.file_size_threshold = 1.5 * 1024 * 1024 * 1024  # bytes

        # Initialize Telegram Application
        self.application = Application.builder().token(self.token).build()

        # Register handlers
        self._register_handlers()

        logger.info("Station10Bot initialized")

    def _register_handlers(self):
        """Register all command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("process", self.process))
        self.application.add_handler(CommandHandler("recent", self.recent))
        self.application.add_handler(CommandHandler("search", self.search))
        self.application.add_handler(CommandHandler("stats", self.stats))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # File upload handlers
        self.application.add_handler(
            MessageHandler(filters.Document.ALL | filters.VIDEO, self.handle_file_upload)
        )

    # ==================== Command Handlers ====================

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register user."""
        user = update.effective_user
        self.db.register_user(
            telegram_id=user.id, username=user.username, full_name=user.full_name
        )

        await update.message.reply_text(
            f"Welcome to Station10 Intelligence!\n\n"
            f"Registered: {user.full_name or user.username}\n"
            f"Monthly budget: $50\n\n"
            f"Commands:\n"
            f"• /process <URL> - Process video from URL\n"
            f"• /recent [N] - Show recent videos\n"
            f"• /search <query> - Search entities\n"
            f"• /stats - Your usage and costs\n"
            f"• /help - Show this help\n\n"
            f"You can also send video files directly (up to 1.5GB)"
        )

    async def process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process video from URL (non-blocking)."""
        if not context.args:
            await update.message.reply_text("Usage: /process <URL>")
            return

        url = context.args[0]
        user = self.db.get_user(update.effective_user.id)

        if not user:
            await update.message.reply_text("Please /start first")
            return

        # Check budget
        used, limit, within = self.db.check_budget(user["id"])
        if not within:
            await update.message.reply_text(
                f"⚠️ Budget exceeded: ${used:.2f}/${limit:.2f}\n"
                f"Contact @zforristall to increase limit"
            )
            return

        # Respond immediately
        status_msg = await update.message.reply_text(
            f"🎬 Processing video...\n\nThis usually takes 2-4 minutes.\n"
            f"I'll notify you when it's done!"
        )

        # Process in background (non-blocking)
        asyncio.create_task(
            self._process_video_background(
                url=url,
                user_id=user["id"],
                chat_id=update.effective_chat.id,
                status_message_id=status_msg.message_id,
            )
        )

    async def handle_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video/document uploads from Telegram."""
        user = self.db.get_user(update.effective_user.id)

        if not user:
            await update.message.reply_text("Please /start first")
            return

        # Check budget
        used, limit, within = self.db.check_budget(user["id"])
        if not within:
            await update.message.reply_text(
                f"⚠️ Budget exceeded: ${used:.2f}/${limit:.2f}\n"
                f"Contact @zforristall to increase limit"
            )
            return

        # Get file object
        file_obj = update.message.document or update.message.video

        if not file_obj:
            await update.message.reply_text("No file found in message")
            return

        file_size = file_obj.file_size

        # Check if file is too large for Telegram download
        if file_size > self.file_size_threshold:
            # File too large - provide signed upload URL
            await update.message.reply_text(
                f"📁 File too large ({file_size / 1e9:.1f}GB)\n\n"
                f"I'll send you an upload link where you can upload directly.\n"
                f"This is more reliable for large files."
            )
            # TODO: Generate and send signed R2 upload URL
            await update.message.reply_text(
                "⚠️ Large file upload not implemented yet.\n"
                "For now, please use /process with a video URL."
            )
            return

        # File is small enough - download via Telegram
        status_msg = await update.message.reply_text(
            f"📥 Downloading {file_obj.file_name or 'video'} ({file_size / 1e6:.1f}MB)...\n"
            f"This may take a moment."
        )

        # Download in background
        asyncio.create_task(
            self._process_uploaded_file_background(
                file_id=file_obj.file_id,
                file_name=file_obj.file_name or f"upload_{file_obj.file_unique_id}.mp4",
                user_id=user["id"],
                chat_id=update.effective_chat.id,
                status_message_id=status_msg.message_id,
            )
        )

    async def recent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent videos."""
        limit = int(context.args[0]) if context.args else 10
        videos = self.db.get_recent_videos(limit)

        if not videos:
            await update.message.reply_text("No videos processed yet")
            return

        text = f"📊 Last {len(videos)} videos:\n\n"
        for v in videos:
            text += f"• {v['title'][:50]}\n"
            text += f"  By: @{v['username']} | Entities: {v['entity_count']}\n\n"

        await update.message.reply_text(text)

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search entities."""
        if not context.args:
            await update.message.reply_text("Usage: /search <entity name>")
            return

        query = " ".join(context.args)
        results = self.db.search_entities(query, limit=10)

        if not results:
            await update.message.reply_text(f"No matches for: {query}")
            return

        text = f"🔍 Found {len(results)} matches for '{query}':\n\n"
        for r in results:
            text += f"• {r['name']} ({r['entity_type']})\n"
            text += f"  Video: {r['title'][:40]}\n"
            text += f"  By: @{r['username']} | {r['processed_at'][:10]}\n\n"

        await update.message.reply_text(text)

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user stats."""
        user = self.db.get_user(update.effective_user.id)

        if not user:
            await update.message.reply_text("Please /start first")
            return

        costs = self.db.get_user_costs(user["id"], days=30)
        used, limit, within = self.db.check_budget(user["id"])

        status = "✅ Within budget" if within else "⚠️ Over budget"

        await update.message.reply_text(
            f"📈 Your Stats (30 days):\n\n"
            f"Videos: {costs.get('video_count', 0)}\n"
            f"Cost: ${used:.2f} / ${limit:.2f}\n"
            f"Avg: ${costs.get('avg_cost', 0):.2f}/video\n\n"
            f"{status}"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message."""
        await update.message.reply_text(
            "🤖 Station10 Dispatch Bot\n\n"
            "Commands:\n"
            "• /process <URL> - Process video from URL\n"
            "• /recent [N] - Show last N videos (default 10)\n"
            "• /search <query> - Search for entities\n"
            "• /stats - View your usage and costs\n"
            "• /help - Show this help\n\n"
            "File Uploads:\n"
            "• Send video/document directly (up to 1.5GB)\n"
            "• Larger files: I'll provide an upload link\n\n"
            "Questions? Contact @zforristall"
        )

    # ==================== Background Processing ====================
    
    def _categorize_error(self, error: Exception) -> tuple[str, str]:
        """
        Categorize error and return (emoji, user_friendly_message).
        
        Returns actionable error messages based on error type.
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Network/Download errors
        if "connection" in error_str or "timeout" in error_str or "network" in error_str:
            return "🌐", "Network error. Please check the URL and try again."
        
        # Video access errors
        if "private" in error_str or "unavailable" in error_str or "not found" in error_str:
            return "🔒", "Video unavailable. It may be private, deleted, or geo-blocked."
        
        # Authentication errors
        if "unauthorized" in error_str or "forbidden" in error_str or "api key" in error_str:
            return "🔑", "API authentication issue. Contact @zforristall."
        
        # Rate limit errors
        if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
            return "⏱️", "API rate limit reached. Try again in a few minutes."
        
        # Processing errors
        if "transcription" in error_str or "voxtral" in error_str:
            return "🎤", "Transcription failed. Audio may be corrupted or unsupported."
        
        if "extraction" in error_str or "grok" in error_str:
            return "🧠", "Intelligence extraction failed. Try again or contact support."
        
        # File format errors
        if "format" in error_str or "codec" in error_str or "decode" in error_str:
            return "📹", "Unsupported video format. Try converting to MP4."
        
        # Database errors
        if "database" in error_str or "sqlite" in error_str:
            return "💾", "Database error. Results may not be saved. Contact @zforristall."
        
        # Memory/Resource errors
        if "memory" in error_str or "resource" in error_str:
            return "💥", "Video too large. Try a shorter video or contact support."
        
        # Generic errors
        return "❌", f"Unexpected error: {error_type}"

    async def _process_video_background(
        self, url: str, user_id: int, chat_id: int, status_message_id: int
    ):
        """Process video in background and notify when complete."""
        bot = Bot(token=self.token)

        try:
            # Process video
            retriever = VideoIntelligenceRetrieverV2(output_dir=str(self.output_dir))
            result = await retriever.process_url(url)

            if result:
                # Save to database
                self.db.add_video(
                    video_id=result.metadata.video_id,
                    url=url,
                    title=result.metadata.title,
                    user_id=user_id,
                    cost=result.processing_cost,
                    entity_count=len(result.entities),
                    relationship_count=len(result.relationships),
                    output_path=result._output_directory
                    if hasattr(result, "_output_directory")
                    else "unknown",
                    channel=result.metadata.channel,
                    duration=result.metadata.duration,
                )

                # Save entities for search
                entities = [
                    {
                        "name": e.name if hasattr(e, "name") else e.get("name"),
                        "type": e.type if hasattr(e, "type") else e.get("type"),
                        "mention_count": e.mention_count
                        if hasattr(e, "mention_count")
                        else e.get("mention_count", 1),
                    }
                    for e in result.entities
                ]
                self.db.add_entities(result.metadata.video_id, entities)

                # Get GCS URL if available
                gcs_url = getattr(result, "gcs_url", None)
                gcs_link = f"\n\n🔗 View: {gcs_url}" if gcs_url else ""

                # Send completion notification
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text=(
                        f"✅ Processing complete!\n\n"
                        f"📹 {result.metadata.title[:100]}\n\n"
                        f"📊 Results:\n"
                        f"• Entities: {len(result.entities)}\n"
                        f"• Relationships: {len(result.relationships)}\n"
                        f"• Cost: ${result.processing_cost:.2f}\n"
                        f"• Duration: {result.metadata.duration}s"
                        f"{gcs_link}"
                    ),
                )
            else:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="❌ Processing failed. Check logs or try again.",
                )

        except Exception as e:
            logger.error(f"Background processing error: {e}", exc_info=True)
            
            # Categorize and format error
            emoji, user_message = self._categorize_error(e)
            error_id = f"err_{int(asyncio.get_event_loop().time())}"
            
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_message_id,
                text=(
                    f"{emoji} Processing Failed\n\n"
                    f"{user_message}\n\n"
                    f"URL: {url[:50]}...\n"
                    f"Error ID: {error_id}\n\n"
                    f"📋 Check logs for details or contact @zforristall"
                ),
            )
            logger.error(f"Error ID {error_id}: {type(e).__name__}: {str(e)}")

    async def _process_uploaded_file_background(
        self,
        file_id: str,
        file_name: str,
        user_id: int,
        chat_id: int,
        status_message_id: int,
    ):
        """Download Telegram file and process in background."""
        bot = Bot(token=self.token)
        temp_dir = None

        try:
            # Download file from Telegram
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_message_id,
                text=f"📥 Downloading {file_name}...",
            )

            file = await bot.get_file(file_id)
            temp_dir = tempfile.mkdtemp(prefix="station10_upload_")
            local_path = Path(temp_dir) / file_name

            await file.download_to_drive(custom_path=str(local_path))

            logger.info(f"Downloaded {file_name} to {local_path}")

            # Update status
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_message_id,
                text=f"🎬 Processing {file_name}...\n\nThis takes 2-4 minutes.",
            )

            # Process the video
            retriever = VideoIntelligenceRetrieverV2(output_dir=str(self.output_dir))
            result = await retriever.process_url(str(local_path))

            if result:
                # Save to database
                self.db.add_video(
                    video_id=result.metadata.video_id,
                    url=f"telegram_upload:{file_id}",
                    title=result.metadata.title or file_name,
                    user_id=user_id,
                    cost=result.processing_cost,
                    entity_count=len(result.entities),
                    relationship_count=len(result.relationships),
                    output_path=result._output_directory
                    if hasattr(result, "_output_directory")
                    else "unknown",
                    channel="Telegram Upload",
                    duration=result.metadata.duration,
                )

                # Save entities
                entities = [
                    {
                        "name": e.name if hasattr(e, "name") else e.get("name"),
                        "type": e.type if hasattr(e, "type") else e.get("type"),
                        "mention_count": e.mention_count
                        if hasattr(e, "mention_count")
                        else e.get("mention_count", 1),
                    }
                    for e in result.entities
                ]
                self.db.add_entities(result.metadata.video_id, entities)

                # Get GCS URL if available
                gcs_url = getattr(result, "gcs_url", None)
                gcs_link = f"\n\n🔗 View: {gcs_url}" if gcs_url else ""

                # Send completion notification
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text=(
                        f"✅ Upload processed!\n\n"
                        f"📹 {result.metadata.title[:100] if result.metadata.title else file_name}\n\n"
                        f"📊 Results:\n"
                        f"• Entities: {len(result.entities)}\n"
                        f"• Relationships: {len(result.relationships)}\n"
                        f"• Cost: ${result.processing_cost:.2f}"
                        f"{gcs_link}"
                    ),
                )
            else:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text="❌ Processing failed. File may be corrupted or unsupported format.",
                )

        except Exception as e:
            logger.error(f"Upload processing error: {e}", exc_info=True)
            
            # Categorize and format error
            emoji, user_message = self._categorize_error(e)
            error_id = f"err_{int(asyncio.get_event_loop().time())}"
            
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_message_id,
                text=(
                    f"{emoji} Upload Processing Failed\n\n"
                    f"{user_message}\n\n"
                    f"File: {file_name}\n"
                    f"Error ID: {error_id}\n\n"
                    f"📋 Check logs for details or contact @zforristall"
                ),
            )
            logger.error(f"Error ID {error_id}: {type(e).__name__}: {str(e)}")
        finally:
            # Clean up temp directory
            if temp_dir and Path(temp_dir).exists():
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)

    async def recent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent videos."""
        limit = int(context.args[0]) if context.args else 10
        videos = self.db.get_recent_videos(limit)

        if not videos:
            await update.message.reply_text("No videos processed yet")
            return

        text = f"📊 Last {len(videos)} videos:\n\n"
        for v in videos:
            text += f"• {v['title'][:50]}\n"
            text += f"  By: @{v['username']} | Entities: {v['entity_count']}\n\n"

        await update.message.reply_text(text)

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search entities."""
        if not context.args:
            await update.message.reply_text("Usage: /search <entity name>")
            return

        query = " ".join(context.args)
        results = self.db.search_entities(query, limit=10)

        if not results:
            await update.message.reply_text(f"No matches for: {query}")
            return

        text = f"🔍 Found {len(results)} matches for '{query}':\n\n"
        for r in results:
            text += f"• {r['name']} ({r['entity_type']})\n"
            text += f"  Video: {r['title'][:40]}\n"
            text += f"  By: @{r['username']} | {r['processed_at'][:10]}\n\n"

        await update.message.reply_text(text)

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user stats."""
        user = self.db.get_user(update.effective_user.id)

        if not user:
            await update.message.reply_text("Please /start first")
            return

        costs = self.db.get_user_costs(user["id"], days=30)
        used, limit, within = self.db.check_budget(user["id"])

        status = "✅ Within budget" if within else "⚠️ Over budget"

        await update.message.reply_text(
            f"📈 Your Stats (30 days):\n\n"
            f"Videos: {costs.get('video_count', 0)}\n"
            f"Cost: ${used:.2f} / ${limit:.2f}\n"
            f"Avg: ${costs.get('avg_cost', 0):.2f}/video\n\n"
            f"{status}"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message."""
        await update.message.reply_text(
            "🤖 Station10 Dispatch Bot\n\n"
            "Commands:\n"
            "• /process <URL> - Process video from URL\n"
            "• /recent [N] - Show last N videos (default 10)\n"
            "• /search <query> - Search for entities\n"
            "• /stats - View your usage and costs\n"
            "• /help - Show this help\n\n"
            "File Uploads:\n"
            "• Send video/document directly (up to 1.5GB)\n"
            "• Larger files: I'll provide an upload link\n\n"
            "Questions? Contact @zforristall"
        )

    # ==================== Webhook Server ====================

    async def webhook_handler(self, request: web.Request) -> web.Response:
        """
        Handle incoming webhook requests from Telegram.
        
        Verifies secret token and processes updates.
        """
        # Verify secret token
        received_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if received_token != self.secret_token:
            logger.warning(f"Invalid secret token from {request.remote}")
            return web.Response(status=403, text="Forbidden")

        try:
            # Parse update
            data = await request.json()
            update = Update.de_json(data, self.application.bot)

            # Process update asynchronously
            await self.application.process_update(update)

            return web.Response(status=200, text="OK")

        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

    async def health_handler(self, request: web.Request) -> web.Response:
        """Health check endpoint for monitoring."""
        return web.Response(status=200, text="OK")

    async def _setup_webhook(self):
        """Set the webhook URL with Telegram."""
        try:
            webhook_info = await self.application.bot.get_webhook_info()
            current_url = webhook_info.url

            target_url = f"{self.webhook_url}/webhook"

            if current_url == target_url:
                logger.info(f"Webhook already set to {target_url}")
            else:
                logger.info(f"Setting webhook to {target_url}")
                await self.application.bot.set_webhook(
                    url=target_url,
                    secret_token=self.secret_token,
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True,
                )
                logger.info("✓ Webhook configured successfully")

        except Exception as e:
            logger.error(f"Failed to set webhook: {e}", exc_info=True)
            raise

    def run(self):
        """Start bot with webhook server."""
        # Create aiohttp web application
        web_app = web.Application()
        web_app.router.add_post("/webhook", self.webhook_handler)
        web_app.router.add_get("/health", self.health_handler)

        # Set up webhook and run server
        async def startup(app):
            """Initialize bot and set webhook on startup."""
            await self.application.initialize()
            await self.application.start()
            await self._setup_webhook()
            logger.info(f"✓ Webhook server starting on port {self.port}")

        async def cleanup(app):
            """Cleanup on shutdown."""
            await self.application.stop()
            await self.application.shutdown()
            logger.info("✓ Bot stopped")

        web_app.on_startup.append(startup)
        web_app.on_cleanup.append(cleanup)

        # Run the web server
        logger.info(f"Starting Station10 Dispatch Bot on port {self.port}")
        logger.info(f"Webhook URL: {self.webhook_url}/webhook")
        
        web.run_app(web_app, host="0.0.0.0", port=self.port)


def main():
    """Entry point for Station10 bot."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    bot = Station10Bot()
    bot.run()


if __name__ == "__main__":
    main()
