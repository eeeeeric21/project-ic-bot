#!/usr/bin/env python3
"""
Project IC Telegram Bot - Render Deployment Version
Includes health check server for Render.
"""

import os
import asyncio
import logging
from aiohttp import web
from telegram.ext import Application

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import the bot setup from telegram_voice_bot
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment from .env if exists (local dev)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except:
    pass

from telegram_voice_bot import setup_bot

# Health check server for Render
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_health_server():
    app = web.Application()
    app.add_routes([web.get('/', health_check), web.get('/health', health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check server running on port {port}")

async def main():
    # Start health check server
    await start_health_server()
    
    # Setup and start the Telegram bot
    application = setup_bot()
    
    # Initialize and start
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("Bot is running!")
    
    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
