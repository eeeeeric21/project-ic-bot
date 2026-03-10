#!/usr/bin/env python3
"""
Project IC Telegram Bot - Render Deployment Version
Includes health check server for Render and API proxy for PWA.
"""

import os
import asyncio
import logging
import json
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
from scheduler import CheckinScheduler

# Environment variables
MERALION_API_URL = os.environ.get("MERALION_API_URL", "http://meralion.org:8010/v1")
MERALION_API_KEY = os.environ.get("MERALION_API_KEY", "")
MERALION_MODEL = os.environ.get("MERALION_MODEL", "MERaLiON/MERaLiON-3-10B")

# API Proxy for PWA
async def api_chat_handler(request):
    """Proxy chat requests to MERaLiON API (avoids CORS issues in browser)."""
    try:
        data = await request.json()
        messages = data.get("messages", [])
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {MERALION_API_KEY}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": MERALION_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150,
            }
            
            async with session.post(
                f"{MERALION_API_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return web.json_response(result)
                else:
                    error_text = await response.text()
                    logger.error(f"MERaLiON API error: {response.status} - {error_text}")
                    return web.json_response(
                        {"error": "API request failed"},
                        status=500
                    )
    except Exception as e:
        logger.error(f"API proxy error: {e}")
        return web.json_response(
            {"error": str(e)},
            status=500
        )

# Health check server for Render
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_health_server():
    app = web.Application()
    
    # CORS middleware for API endpoint
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == "OPTIONS":
                response = web.Response()
            else:
                response = await handler(request)
            
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response
        return middleware_handler
    
    app.middlewares.append(cors_middleware)
    
    app.add_routes([
        web.get('/', health_check),
        web.get('/health', health_check),
        web.post('/api/chat', api_chat_handler),
        web.options('/api/chat', api_chat_handler),
    ])
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check server + API proxy running on port {port}")

async def main():
    # Start health check server + API proxy
    await start_health_server()
    
    # Setup and start the Telegram bot
    application = setup_bot()
    
    # Initialize and start
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("Bot is running!")
    
    # Start the check-in scheduler in background
    scheduler = CheckinScheduler()
    scheduler.load_patients()
    asyncio.create_task(scheduler.run_scheduler())
    logger.info("Check-in scheduler started (8 AM, 2 PM, 8 PM, weekly reports)")
    
    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
