"""
Station10 Intelligence Bot - Multi-user Telegram interface

Commands:
- /start - Register as Station10 user
- /process <URL> - Process video
- /recent [N] - Last N videos
- /search <query> - Search entities
- /stats - Your usage and costs
"""

import os
import logging
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

from ..database.db_manager import Station10Database
from ..retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2

logger = logging.getLogger(__name__)


class Station10Bot:
    """Multi-user Telegram bot for Station10 Media."""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.db = Station10Database()
        self.output_dir = "output/station10"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register user."""
        user = update.effective_user
        user_id = self.db.register_user(
            telegram_id=user.id,
            username=user.username,
            full_name=user.full_name
        )
        
        await update.message.reply_text(
            f"Welcome to Station10 Intelligence Platform!\n\n"
            f"Registered: {user.full_name or user.username}\n"
            f"Monthly budget: $50\n\n"
            f"Commands:\n"
            f"/process <URL> - Process video\n"
            f"/recent [N] - Recent videos\n"
            f"/search <query> - Search entities\n"
            f"/stats - Your usage\n"
            f"/help - Command help"
        )
    
    async def process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process video."""
        if not context.args:
            await update.message.reply_text("Usage: /process <URL>")
            return
        
        url = context.args[0]
        user = self.db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("Please /start first")
            return
        
        # Check budget
        used, limit, within = self.db.check_budget(user['id'])
        if not within:
            await update.message.reply_text(
                f"Budget exceeded: ${used:.2f}/${limit:.2f}\n"
                f"Contact @zforristall to increase limit"
            )
            return
        
        # Queue processing
        await update.message.reply_text(f"Processing {url}...\n\nThis takes 3-5 minutes.")
        
        try:
            # Process video
            retriever = VideoIntelligenceRetrieverV2(output_dir=self.output_dir)
            result = await retriever.process_url(url)
            
            if result:
                # Save to database
                self.db.add_video(
                    video_id=result.metadata.video_id,
                    url=url,
                    title=result.metadata.title,
                    user_id=user['id'],
                    cost=result.processing_cost,
                    entity_count=len(result.entities),
                    relationship_count=len(result.relationships),
                    output_path=result._output_directory if hasattr(result, '_output_directory') else 'unknown',
                    channel=result.metadata.channel,
                    duration=result.metadata.duration
                )
                
                # Save entities for search
                entities = [{'name': e.name if hasattr(e, 'name') else e.get('name'),
                           'type': e.type if hasattr(e, 'type') else e.get('type'),
                           'mention_count': e.mention_count if hasattr(e, 'mention_count') else e.get('mention_count', 1)}
                          for e in result.entities]
                self.db.add_entities(result.metadata.video_id, entities)
                
                # Send result
                await update.message.reply_text(
                    f"✅ Processed: {result.metadata.title}\n\n"
                    f"Entities: {len(result.entities)}\n"
                    f"Relationships: {len(result.relationships)}\n"
                    f"Cost: ${result.processing_cost:.2f}\n\n"
                    f"Use /search to query entities"
                )
            else:
                await update.message.reply_text("Processing failed. Check logs.")
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            await update.message.reply_text(f"Error: {e}")
    
    async def recent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent videos."""
        limit = int(context.args[0]) if context.args else 10
        videos = self.db.get_recent_videos(limit)
        
        if not videos:
            await update.message.reply_text("No videos processed yet")
            return
        
        text = f"Last {len(videos)} videos:\n\n"
        for v in videos:
            text += f"• {v['title'][:50]}\n"
            text += f"  By: @{v['username']} | Entities: {v['entity_count']}\n\n"
        
        await update.message.reply_text(text)
    
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search entities."""
        if not context.args:
            await update.message.reply_text("Usage: /search <entity name>")
            return
        
        query = ' '.join(context.args)
        results = self.db.search_entities(query, limit=10)
        
        if not results:
            await update.message.reply_text(f"No matches for: {query}")
            return
        
        text = f"Found {len(results)} matches for '{query}':\n\n"
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
        
        costs = self.db.get_user_costs(user['id'], days=30)
        used, limit, within = self.db.check_budget(user['id'])
        
        status = "✅ Within budget" if within else "⚠️ Over budget"
        
        await update.message.reply_text(
            f"Your Stats (30 days):\n\n"
            f"Videos: {costs.get('video_count', 0)}\n"
            f"Cost: ${used:.2f} / ${limit:.2f}\n"
            f"Avg: ${costs.get('avg_cost', 0):.2f}/video\n\n"
            f"{status}"
        )
    
    def run(self):
        """Start bot with webhook (for Cloud Run)."""
        app = Application.builder().token(self.token).build()
        
        # Register handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("process", self.process))
        app.add_handler(CommandHandler("recent", self.recent))
        app.add_handler(CommandHandler("search", self.search))
        app.add_handler(CommandHandler("stats", self.stats))
        
        # Run with webhook for Cloud Run
        port = int(os.getenv("PORT", 8080))
        webhook_url = os.getenv("WEBHOOK_URL")  # https://your-cloud-run-url.run.app
        
        if webhook_url:
            logger.info(f"Starting webhook on port {port}")
            app.run_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=f"{webhook_url}/webhook",
                allowed_updates=Update.ALL_TYPES
            )
        else:
            logger.info("Starting polling (development mode)")
            app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = Station10Bot()
    bot.run()
EOF

echo "Station10 bot created - ready for Cloud Run deployment"

