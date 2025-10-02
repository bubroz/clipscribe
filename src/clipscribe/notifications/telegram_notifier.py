"""
Telegram notifications for new X drafts.

Sends notifications when video processing completes.
User taps button to review draft on mobile.
"""

import logging
import os
from typing import Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Send Telegram notifications for new X drafts.
    
    Setup:
    1. Get bot token from @BotFather on Telegram
    2. Set TELEGRAM_BOT_TOKEN env var
    3. Set TELEGRAM_CHAT_ID env var (your user ID)
    4. Start using
    """
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set - notifications disabled")
            self.enabled = False
        elif not self.chat_id:
            logger.warning("TELEGRAM_CHAT_ID not set - notifications disabled")
            self.enabled = False
        else:
            self.bot = Bot(token=self.bot_token)
            self.enabled = True
            logger.info("TelegramNotifier initialized and ready")
    
    async def notify_draft_ready(
        self,
        title: str,
        entity_count: int,
        relationship_count: int,
        char_count: int,
        draft_url: str
    ):
        """
        Send notification when X draft is ready.
        
        Args:
            title: Video title
            entity_count: Number of entities extracted
            relationship_count: Number of relationships
            char_count: Tweet character count
            draft_url: URL to draft review page
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled, skipping")
            return
        
        try:
            # Format message
            message = f"""🎬 New X draft ready

{title}

📊 Intel:
• {entity_count} entities
• {relationship_count} relationships
• {char_count} character tweet

Tap below to review:"""
            
            # Create inline button
            keyboard = [[
                InlineKeyboardButton("📱 Review Draft", url=draft_url),
                InlineKeyboardButton("❌ Skip", callback_data=f"skip_{draft_url}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send message
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                reply_markup=reply_markup
            )
            
            logger.info(f"Sent Telegram notification for: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    
    async def notify_processing_started(self, title: str):
        """Quick notification when processing starts."""
        if not self.enabled:
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"⏳ Processing: {title}..."
            )
        except Exception as e:
            logger.debug(f"Failed to send processing notification: {e}")
    
    async def notify_error(self, title: str, error: str):
        """Notify when processing fails."""
        if not self.enabled:
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"❌ Failed: {title}\n\nError: {error}"
            )
        except Exception as e:
            logger.debug(f"Failed to send error notification: {e}")
    
    def get_chat_id(self) -> Optional[str]:
        """
        Helper to find your Telegram chat ID.
        
        Usage:
        1. Message your bot on Telegram
        2. Run: python -c "from clipscribe.notifications.telegram_notifier import get_my_chat_id; get_my_chat_id()"
        3. Copy the ID shown
        4. Set TELEGRAM_CHAT_ID env var
        """
        return self.chat_id


async def get_my_chat_id():
    """Find your Telegram chat ID."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not set")
        return
    
    bot = Bot(token=bot_token)
    updates = await bot.get_updates()
    
    if updates:
        chat_id = updates[-1].message.chat.id
        print(f"Your Telegram chat ID: {chat_id}")
        print(f"Set it: export TELEGRAM_CHAT_ID={chat_id}")
    else:
        print("No messages found. Send a message to your bot first!")


if __name__ == "__main__":
    # Test notifier
    asyncio.run(get_my_chat_id())

