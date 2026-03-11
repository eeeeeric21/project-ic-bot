#!/usr/bin/env python3
"""
Project IC Telegram Voice Bot
Real-time check-in bot with voice message support.

Features:
- Accepts voice messages from patients
- Transcribes using MERaLiON ASR
- Responds via text (and optional TTS)
- Sends alerts to case workers

Usage:
    python telegram_voice_bot.py
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv
from typing import Dict, Optional

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

import aiohttp
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import our modules
sys.path.insert(0, str(Path(__file__).parent))
from generate_response import (
    PatientContext,
    ConversationContext,
    generate_response,
    generate_fallback_response
)
from analyze import analyze_response
from voice_service import TTSService, TTSProvider, ASRService
from scheduler import CheckinScheduler, Patient

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global scheduler instance (set by bot_server.py)
scheduler: CheckinScheduler = None

def set_scheduler(s: CheckinScheduler):
    """Set the scheduler instance (called from bot_server.py)."""
    global scheduler
    scheduler = s

# Environment variables
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CASE_WORKER_CHAT_ID = os.environ.get("TELEGRAM_CASE_WORKER_CHAT_ID")
MERALION_API_URL = os.environ.get("MERALION_API_URL")
MERALION_API_KEY = os.environ.get("MERALION_API_KEY")

# In-memory session storage (in production, use database)
active_sessions: Dict[int, Dict] = {}

# Wake words/phrases that trigger check-in
WAKE_WORDS = [
    "hello aescul",
    "hello aesculai",
    "hello aescul helper",
    "hi aescul",
    "hey aescul",
    "aescul helper",
    "start check in",
    "start check-in",
]

# Demo patient mapping (in production, link telegram_id to patient in DB)
PATIENT_MAPPING = {
    # telegram_id: patient_id
    # Will be populated as users register
}


class VoiceTranscriber:
    """Handle voice message transcription using MERaLiON ASR."""
    
    def __init__(self):
        self.api_url = MERALION_API_URL
        self.api_key = MERALION_API_KEY
        self.asr_model = "MERaLiON/MERaLiON-2-10B-ASR"
    
    async def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe audio using MERaLiON ASR.
        
        Args:
            audio_data: Raw audio bytes (OGG format from Telegram)
        
        Returns:
            Transcribed text
        """
        if not self.api_url or not self.api_key:
            logger.warning("MERaLiON API not configured")
            return ""
        
        try:
            import base64
            
            async with aiohttp.ClientSession() as session:
                # MERaLiON ASR endpoint
                # Note: Actual endpoint may differ, adjust based on docs
                url = f"{self.api_url.replace('/v1', '')}/asr/transcribe"
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                }
                
                # Encode audio as base64
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                payload = {
                    "model": self.asr_model,
                    "audio": audio_base64,
                    "language": "en",  # Can be 'zh', 'ms', 'ta' for other languages
                }
                
                async with session.post(url, headers=headers, json=payload, 
                                       timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("text", "")
                    else:
                        logger.error(f"ASR error: {resp.status}")
                        return ""
                        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    async def transcribe_with_emotion(self, audio_data: bytes) -> Dict:
        """
        Transcribe audio and detect emotion.
        
        Returns:
            {
                "text": str,
                "emotion": str,
                "confidence": float
            }
        """
        # For now, just transcribe
        # TODO: Add emotion detection when MERaLiON AudioLLM endpoint is available
        text = await self.transcribe(audio_data)
        return {
            "text": text,
            "emotion": "neutral",
            "confidence": 0.5
        }


# Initialize services
transcriber = ASRService()
tts_service = TTSService(TTSProvider.EDGE)  # Free TTS, no API key needed

# Voice output setting
VOICE_OUTPUT_ENABLED = os.environ.get("VOICE_OUTPUT", "true").lower() == "true"


def get_or_create_session(telegram_id: str, user_name: str) -> Dict:
    """Get or create a check-in session for a user."""
    telegram_id = str(telegram_id)  # Ensure string
    
    if telegram_id not in active_sessions:
        # Create demo patient (in production, fetch from DB)
        patient = PatientContext(
            patient_id=f"telegram-{telegram_id}",
            name=user_name,
            preferred_name=user_name,
            age=70,
            conditions=[],
            medications=[],
            interests=[],
            family_members=[],
            recent_concerns=[]
        )
        
        session = {
            "patient": patient,
            "messages": [],
            "signals": [],
            "risk_score": 0,
            "started_at": datetime.now().isoformat()
        }
        active_sessions[telegram_id] = session
    
    return active_sessions[telegram_id]


async def send_case_worker_alert(patient_name: str, risk_level: str, score: int, signals: list):
    """Send alert to case worker via Telegram."""
    if not BOT_TOKEN or not CASE_WORKER_CHAT_ID:
        logger.warning("Case worker not configured")
        return
    
    emoji = {"RED": "🚨", "ORANGE": "⚠️", "YELLOW": "📋"}.get(risk_level, "ℹ️")
    
    message = f"""{emoji} *Project IC Alert*

*Patient:* {patient_name}
*Level:* {risk_level}
*Score:* {score}

*Issues Detected:*
{chr(10).join(f'• {s}' for s in signals)}

_Time: {datetime.now().strftime('%H:%M on %d %b %Y')}_
"""
    
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        await session.post(url, json={
            "chat_id": CASE_WORKER_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        })


# Bot Command Handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Register patient for daily check-ins
    if telegram_id not in scheduler.patients:
        scheduler.register_patient(telegram_id, user.first_name)
        await update.message.reply_text(
            f"✅ Registered you for daily check-ins!\n\n"
            f"You'll receive:\n"
            f"• Morning check-in at 8:00 AM 🌅\n"
            f"• Afternoon check-in at 2:00 PM 🌤️\n\n"
            f"You can also start a check-in anytime by saying:\n"
            f'"Hello Aescul Helper"',
            parse_mode='Markdown'
        )
    
    # Create session
    session = get_or_create_session(telegram_id, user.first_name)
    
    welcome_message = f"""Hello {user.first_name}! 👋

I'm your AI health companion. I check in on you daily to make sure you're doing well.

*Daily Check-ins:*
• 🌅 Morning: 8:00 AM
• 🌤️ Afternoon: 2:00 PM

*How to use:*
• Say "Hello Aescul Helper" to start a check-in 🗣️
• Or send me a voice message 🎤
• Or type a message 💬

*Commands:*
/end - End current check-in
/status - View your health status

Let's start! How are you feeling today?"""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    # Track message
    session["messages"].append({
        "role": "assistant",
        "content": welcome_message,
        "timestamp": datetime.now().isoformat()
    })


async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /end command to complete check-in."""
    user = update.effective_user
    telegram_id = str(user.id)
    
    if telegram_id not in active_sessions:
        await update.message.reply_text("No active check-in session. Send a message to start!")
        return
    
    session = active_sessions[telegram_id]
    score = session["risk_score"]
    
    # Determine risk level
    if score >= 50:
        risk_level = "RED"
        emoji = "🔴"
    elif score >= 30:
        risk_level = "ORANGE"
        emoji = "🟠"
    elif score >= 15:
        risk_level = "YELLOW"
        emoji = "🟡"
    else:
        risk_level = "GREEN"
        emoji = "🟢"
    
    # Build summary message
    message_count = len([m for m in session['messages'] if m['role'] == 'user'])
    closing_msg = "Thank you for checking in! Take care! 💙" if risk_level == "GREEN" else "I've noted your concerns. Take care!"
    
    summary = f"""{emoji} *Check-in Complete!*

*Summary:*
• Messages: {message_count}
• Risk Level: {risk_level}
• Score: {score}/100

{closing_msg}

See you tomorrow! 🌅"""
    
    await update.message.reply_text(summary, parse_mode='Markdown')
    
    # Send alert if needed
    if risk_level in ["ORANGE", "RED"]:
        await send_case_worker_alert(
            session["patient"].preferred_name,
            risk_level,
            score,
            list(set(session["signals"]))
        )
    
    # Clear session
    del active_sessions[telegram_id]


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    user = update.effective_user
    telegram_id = str(user.id)
    
    if telegram_id not in active_sessions:
        await update.message.reply_text("No active session. Use /start to begin a check-in!")
        return
    
    session = active_sessions[telegram_id]
    
    status_msg = f"""📊 *Current Session Status*

• Risk Score: {session['risk_score']}
• Signals: {', '.join(set(session['signals'])) if session['signals'] else 'None'}
• Messages: {len(session['messages'])}

Continue chatting or use /end to finish."""
    
    await update.message.reply_text(status_msg, parse_mode='Markdown')


# ============================================
# MEDICATION COMMANDS (for Case Workers)
# ============================================

# Store pending medication additions for confirmation
pending_medications: Dict[str, Dict] = {}


async def addmed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addmed command to add medication for a patient.
    
    Usage: /addmed <patient_name> <name> <dosage> <times>
    Example: /addmed Eric Metformin 500mg 08:00,20:00
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Only allow case workers
    if telegram_id != CASE_WORKER_CHAT_ID:
        await update.message.reply_text("⚠️ This command is for case workers only.")
        return
    
    if not context.args or len(context.args) < 4:
        await update.message.reply_text(
            "💊 *Add Medication*\n\n"
            "Usage: `/addmed <patient_name> <med_name> <dosage> <times>`\n\n"
            "Example: `/addmed Eric Metformin 500mg 08:00,20:00`\n\n"
            "Times should be comma-separated (24-hour format).",
            parse_mode='Markdown'
        )
        return
    
    patient_identifier = context.args[0]
    med_name = context.args[1]
    dosage = context.args[2]
    times_str = context.args[3]
    instructions = " ".join(context.args[4:]) if len(context.args) > 4 else ""
    
    # Look up patient by name or ID
    patient = None
    patient_id = None
    
    # First try exact ID match
    if patient_identifier in scheduler.patients:
        patient = scheduler.patients[patient_identifier]
        patient_id = patient_identifier
    else:
        # Search by name (case-insensitive)
        matches = []
        for tid, p in scheduler.patients.items():
            if patient_identifier.lower() in p.name.lower() or patient_identifier.lower() in p.preferred_name.lower():
                matches.append((tid, p))
        
        if len(matches) == 1:
            patient_id, patient = matches[0]
        elif len(matches) > 1:
            # Multiple matches - show selection
            keyboard = []
            for tid, p in matches:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{p.name} ({p.preferred_name})",
                        callback_data=f"addmed_select|{tid}|{med_name}|{dosage}|{times_str}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="addmed_cancel")])
            
            await update.message.reply_text(
                f"👥 *Multiple patients match \"{patient_identifier}\"*\n\nPlease select:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        else:
            # No match found
            await update.message.reply_text(
                f"⚠️ Patient \"{patient_identifier}\" not found.\n\n"
                f"Registered patients:\n"
                + "\n".join(f"• {p.name} ({p.preferred_name})" for p in scheduler.patients.values()),
                parse_mode='Markdown'
            )
            return
    
    # Parse times
    times = [t.strip() for t in times_str.split(',')]
    
    # Validate times
    for t in times:
        try:
            hour, minute = map(int, t.split(':'))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError()
        except:
            await update.message.reply_text(f"⚠️ Invalid time format: {t}. Use HH:MM format.")
            return
    
    # Show confirmation message with inline buttons
    confirmation_msg = f"""💊 *Confirm Add Medication?*

*Patient:* {patient.name} ({patient.preferred_name})
*Medication:* {med_name}
*Dosage:* {dosage}
*Reminder times:* {', '.join(times)}"""
    
    if instructions:
        confirmation_msg += f"\n*Instructions:* {instructions}"
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"addmed_confirm|{patient_id}|{med_name}|{dosage}|{times_str}"),
            InlineKeyboardButton("❌ Cancel", callback_data="addmed_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        confirmation_msg,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def addmed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle medication confirmation callback."""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    query = update.callback_query
    await query.answer()
    
    telegram_id = str(query.from_user.id)
    
    # Only allow case workers
    if telegram_id != CASE_WORKER_CHAT_ID:
        await query.edit_message_text("⚠️ This action is for case workers only.")
        return
    
    data = query.data
    
    if data == "addmed_cancel":
        await query.edit_message_text("❌ *Cancelled*\n\nMedication was not added.", parse_mode='Markdown')
        return
    
    # Handle patient selection from multiple matches
    if data.startswith("addmed_select|"):
        # Parse: addmed_select|patient_id|med_name|dosage|times
        parts = data.split("|")
        if len(parts) >= 5:
            patient_id = parts[1]
            med_name = parts[2]
            dosage = parts[3]
            times_str = parts[4]
            times = [t.strip() for t in times_str.split(',')]
            
            # Get patient info
            patient = scheduler.patients.get(patient_id)
            if not patient:
                await query.edit_message_text("⚠️ Patient not found.", parse_mode='Markdown')
                return
            
            # Show confirmation
            confirmation_msg = f"""💊 *Confirm Add Medication?*

*Patient:* {patient.name} ({patient.preferred_name})
*Medication:* {med_name}
*Dosage:* {dosage}
*Reminder times:* {', '.join(times)}"""
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm", callback_data=f"addmed_confirm|{patient_id}|{med_name}|{dosage}|{times_str}"),
                    InlineKeyboardButton("❌ Cancel", callback_data="addmed_cancel")
                ]
            ]
            
            await query.edit_message_text(
                confirmation_msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return
    
    if data.startswith("addmed_confirm|"):
        # Parse callback data (using | as separator to handle colons in times)
        parts = data.split("|")
        if len(parts) >= 5:
            patient_id = parts[1]
            med_name = parts[2]
            dosage = parts[3]
            times_str = parts[4]
            times = [t.strip() for t in times_str.split(',')]
            
            # Add medication (to Supabase if available)
            if scheduler.medication_manager:
                medication = await scheduler.medication_manager.add_medication_async(
                    patient_id, med_name, dosage, "", times, created_by=telegram_id
                )
                
                # Get patient name
                patient_name = patient_id
                if patient_id in scheduler.patients:
                    patient_name = scheduler.patients[patient_id].name
                
                await query.edit_message_text(
                    f"✅ *Medication Added Successfully!*\n\n"
                    f"• Patient: {patient_name}\n"
                    f"• Medication: {med_name} ({dosage})\n"
                    f"• Reminder times: {', '.join(times)}\n\n"
                    f"The patient will receive reminders at the scheduled times.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "⚠️ Medication system not available.",
                    parse_mode='Markdown'
                )
        else:
            await query.edit_message_text("⚠️ Invalid confirmation data.", parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ Medication system not available.")


async def listmed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listmed command to list medications for a patient.
    
    Usage: /listmed [patient_name]
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Determine which patient to show
    if context.args:
        patient_identifier = context.args[0]
        
        # Look up patient by ID or name
        patient_id = None
        if patient_identifier in scheduler.patients:
            patient_id = patient_identifier
        else:
            # Search by name
            for tid, p in scheduler.patients.items():
                if patient_identifier.lower() in p.name.lower() or patient_identifier.lower() in p.preferred_name.lower():
                    patient_id = tid
                    break
        
        if not patient_id:
            await update.message.reply_text(
                f"⚠️ Patient \"{patient_identifier}\" not found.\n\n"
                f"Registered patients:\n"
                + "\n".join(f"• {p.name}" for p in scheduler.patients.values()),
                parse_mode='Markdown'
            )
            return
        
        # Only allow case workers or self
        if telegram_id != CASE_WORKER_CHAT_ID and patient_id != telegram_id:
            await update.message.reply_text("⚠️ You can only view your own medications.")
            return
    else:
        patient_id = telegram_id
    
    if not scheduler.medication_manager:
        await update.message.reply_text("⚠️ Medication system not available.")
        return
    
    medications = scheduler.medication_manager.medications.get(patient_id, [])
    
    # Get patient name
    patient_name = patient_id
    if patient_id in scheduler.patients:
        patient_name = scheduler.patients[patient_id].name
    
    if not medications:
        await update.message.reply_text(f"📋 No medications registered for {patient_name}.")
        return
    
    msg = f"💊 *Medications for {patient_name}*\n\n"
    for med in medications:
        status = "✅" if med.active else "❌"
        msg += f"{status} {med.name} ({med.dosage})\n"
        msg += f"   ⏰ {', '.join(med.reminder_times)}\n"
        if med.instructions:
            msg += f"   📝 {med.instructions}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def adherence_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adherence command to view medication adherence.
    
    Usage: /adherence <patient_id>
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Only allow case workers
    if telegram_id != CASE_WORKER_CHAT_ID:
        await update.message.reply_text("⚠️ This command is for case workers only.")
        return
    
    patient_id = context.args[0] if context.args else None
    
    if not patient_id:
        await update.message.reply_text("Usage: /adherence <patient_name>")
        return
    
    # Look up patient by name
    patient = scheduler.patients.get(patient_id)
    if not patient:
        # Try name search
        for tid, p in scheduler.patients.items():
            if patient_id.lower() in p.name.lower() or patient_id.lower() in p.preferred_name.lower():
                patient = p
                patient_id = tid
                break
    
    if not patient:
        await update.message.reply_text(f"⚠️ Patient \"{patient_id}\" not found.")
        return
    
    if not scheduler.medication_manager:
        await update.message.reply_text("⚠️ Medication system not available.")
        return
    
    report = await scheduler.medication_manager.get_adherence_report(patient_id)
    
    rate_emoji = "🟢" if report['adherence_rate'] >= 80 else "🟡" if report['adherence_rate'] >= 50 else "🔴"
    
    msg = f"""📊 *Medication Adherence Report*

*Patient:* {patient.name}
*Period:* Last {report['period_days']} days

{rate_emoji} *Overall Adherence: {report['adherence_rate']}%*

• ✅ Taken: {report['taken']}
• ⏭️ Skipped: {report['skipped']}
• ❌ Missed: {report['missed']}
• 📋 Total doses: {report['total_doses']}"""
    
    # Add per-medication breakdown
    if report.get('by_medication'):
        msg += "\n\n*By Medication:*\n"
        for med_name, stats in report['by_medication'].items():
            total = stats['taken'] + stats['skipped'] + stats['missed']
            if total > 0:
                taken_pct = (stats['taken'] / total * 100) if total > 0 else 0
                med_emoji = "✅" if taken_pct >= 80 else "⚠️" if taken_pct >= 50 else "❌"
                msg += f"\n{med_emoji} {med_name}\n"
                msg += f"  Taken: {stats['taken']} | Skipped: {stats['skipped']} | Missed: {stats['missed']}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def delmed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delmed command to delete a medication.
    
    Usage: /delmed <patient_name> <medication_name>
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Only allow case workers
    if telegram_id != CASE_WORKER_CHAT_ID:
        await update.message.reply_text("⚠️ This command is for case workers only.")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "🗑️ *Delete Medication*\n\n"
            "Usage: `/delmed <patient_name> <medication_name>`\n\n"
            "Example: `/delmed Eric Metformin`",
            parse_mode='Markdown'
        )
        return
    
    patient_identifier = context.args[0]
    med_name = " ".join(context.args[1:])
    
    # Look up patient
    patient = None
    patient_id = None
    
    if patient_identifier in scheduler.patients:
        patient = scheduler.patients[patient_identifier]
        patient_id = patient_identifier
    else:
        for tid, p in scheduler.patients.items():
            if patient_identifier.lower() in p.name.lower() or patient_identifier.lower() in p.preferred_name.lower():
                patient_id = tid
                patient = p
                break
    
    if not patient:
        await update.message.reply_text(f"⚠️ Patient \"{patient_identifier}\" not found.")
        return
    
    if not scheduler.medication_manager:
        await update.message.reply_text("⚠️ Medication system not available.")
        return
    
    # Find medications matching the name
    medications = scheduler.medication_manager.medications.get(patient_id, [])
    matching = [m for m in medications if med_name.lower() in m.name.lower()]
    
    if not matching:
        await update.message.reply_text(
            f"⚠️ No medication matching \"{med_name}\" found for {patient.name}.\n\n"
            f"Use `/listmed {patient.name}` to see all medications.",
            parse_mode='Markdown'
        )
        return
    
    if len(matching) == 1:
        # Single match - show confirmation
        med = matching[0]
        keyboard = [[
            InlineKeyboardButton("🗑️ Delete", callback_data=f"delmed_confirm|{patient_id}|{med.id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="delmed_cancel")
        ]]
        
        await update.message.reply_text(
            f"🗑️ *Delete Medication?*\n\n"
            f"*Patient:* {patient.name}\n"
            f"*Medication:* {med.name} ({med.dosage})\n"
            f"*Times:* {', '.join(med.reminder_times)}\n\n"
            f"⚠️ This cannot be undone.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Multiple matches - show selection
        keyboard = []
        for med in matching:
            keyboard.append([InlineKeyboardButton(
                f"{med.name} ({med.dosage}) - {', '.join(med.reminder_times)}",
                callback_data=f"delmed_confirm|{patient_id}|{med.id}"
            )])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="delmed_cancel")])
        
        await update.message.reply_text(
            f"🗑️ *Select medication to delete:*\n\n"
            f"Patient: {patient.name}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def delmed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle medication deletion callback."""
    query = update.callback_query
    await query.answer()
    
    telegram_id = str(query.from_user.id)
    
    if telegram_id != CASE_WORKER_CHAT_ID:
        await query.edit_message_text("⚠️ This action is for case workers only.")
        return
    
    data = query.data
    
    if data == "delmed_cancel":
        await query.edit_message_text("❌ *Cancelled*\n\nMedication was not deleted.", parse_mode='Markdown')
        return
    
    if data.startswith("delmed_confirm|"):
        parts = data.split("|")
        if len(parts) >= 3:
            patient_id = parts[1]
            med_id = parts[2]
            
            # Delete medication from Supabase
            if scheduler.medication_manager:
                # Find medication name before deleting
                medications = scheduler.medication_manager.medications.get(patient_id, [])
                deleted_name = "Medication"
                deleted_dosage = ""
                for med in medications:
                    if med.id == med_id:
                        deleted_name = med.name
                        deleted_dosage = med.dosage
                        break
                
                # Delete from Supabase
                success = await scheduler.medication_manager.delete_medication_async(patient_id, med_id)
                
                if success:
                    patient_name = patient_id
                    if patient_id in scheduler.patients:
                        patient_name = scheduler.patients[patient_id].name
                    
                    await query.edit_message_text(
                        f"✅ *Medication Deleted*\n\n"
                        f"• {deleted_name} ({deleted_dosage})\n"
                        f"• Removed from {patient_name}'s schedule",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text("⚠️ Failed to delete medication.", parse_mode='Markdown')
            else:
                await query.edit_message_text("⚠️ Medication system not available.", parse_mode='Markdown')
        else:
            await query.edit_message_text("⚠️ Invalid medication data.", parse_mode='Markdown')


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages."""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Get or create session
    session = get_or_create_session(telegram_id, user.first_name)
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=telegram_id, action="typing")
    
    # Get voice file
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    
    # Download audio
    audio_data = BytesIO()
    await file.download_to_memory(audio_data)
    audio_bytes = audio_data.getvalue()
    
    # Transcribe using MERaLiON ASR
    await context.bot.send_chat_action(chat_id=telegram_id, action="typing")
    
    transcription = await transcriber.transcribe(audio_bytes)
    
    if not transcription:
        await update.message.reply_text(
            "Sorry, I couldn't understand that. Could you try again? 🙏"
        )
        return
    
    # Process the transcribed text directly (don't show transcription)
    await process_text_message(update, context, transcription, is_voice=True)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    user = update.effective_user
    telegram_id = str(user.id)
    text = update.message.text
    
    # Process the message
    await process_text_message(update, context, text, is_voice=False)


async def process_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               text: str, is_voice: bool = False):
    """Process a text message (from voice transcription or direct text)."""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Check for wake words
    text_lower = text.lower().strip()
    is_wake_word = any(wake in text_lower for wake in WAKE_WORDS)
    
    # === MEDICATION RESPONSE HANDLING ===
    # Check if this is a response to a medication reminder
    if scheduler and scheduler.medication_manager:
        for reminder_id, reminder in list(scheduler.medication_manager.pending_reminders.items()):
            if reminder.patient_id == telegram_id and reminder.status == "pending":
                if text_lower in ["taken", "ok", "yes", "done", "took it", "took"]:
                    scheduler.medication_manager.mark_taken(telegram_id, reminder_id)
                    await update.message.reply_text(
                        "✅ *Recorded!*\n\nGreat job staying on top of your medication! 💙",
                        parse_mode='Markdown'
                    )
                    return
                elif text_lower in ["skip", "skipped", "no", "missed"]:
                    scheduler.medication_manager.mark_skipped(telegram_id, "", reminder_id)
                    await update.message.reply_text(
                        "📝 *Noted*\n\nIf you're feeling unwell, please let me know. Take care! 💙",
                        parse_mode='Markdown'
                    )
                    return
    
    if is_wake_word:
        # Start a fresh check-in session
        if telegram_id in active_sessions:
            del active_sessions[telegram_id]
        
        greeting = f"Hello {user.first_name}! 👋 How are you feeling today?"
        
        # Create new session
        session = get_or_create_session(telegram_id, user.first_name)
        session["messages"].append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send voice + text response
        if VOICE_OUTPUT_ENABLED:
            voice_audio = await tts_service.synthesize(greeting)
            if voice_audio:
                await update.message.reply_voice(
                    voice=BytesIO(voice_audio),
                    caption=greeting
                )
                return
        
        await update.message.reply_text(greeting)
        return
    
    # Get session
    session = get_or_create_session(telegram_id, user.first_name)
    patient = session["patient"]
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=telegram_id, action="typing")
    
    # Analyze message
    analysis = analyze_response(text)
    
    # Update risk score
    session["risk_score"] += analysis.risk_score
    
    # Track signals
    if analysis.detected_categories:
        session["signals"].extend(analysis.detected_categories)
    
    # Build conversation context
    conversation = ConversationContext(
        session_type="ad-hoc",
        previous_messages=session["messages"],
        current_analysis={
            "detected_categories": analysis.detected_categories,
            "risk_score": analysis.risk_score,
            "signals": analysis.signals
        }
    )
    
    # Get AI response
    try:
        ai_response = await generate_response(patient, conversation, text)
    except Exception as e:
        logger.error(f"Generate response error: {e}")
        ai_response = generate_fallback_response({
            "detected_categories": analysis.detected_categories
        })
    
    # Store messages
    session["messages"].append({
        "role": "user",
        "content": text,
        "is_voice": is_voice,
        "timestamp": datetime.now().isoformat()
    })
    session["messages"].append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    
    # Send response (text + voice if enabled)
    if VOICE_OUTPUT_ENABLED and is_voice:
        # Generate voice response
        voice_audio = await tts_service.synthesize(ai_response)
        
        if voice_audio:
            # Send voice message
            await update.message.reply_voice(
                voice=BytesIO(voice_audio),
                caption=ai_response,
                read_timeout=30,
                write_timeout=30
            )
        else:
            # Fallback to text only
            await update.message.reply_text(ai_response)
    else:
        # Text only
        await update.message.reply_text(ai_response)
    
    # Check if alert needed
    if session["risk_score"] >= 30:
        await update.message.reply_text(
            "🙏 I'm concerned about what you've shared. I'll make sure someone checks in on you."
        )
        await send_case_worker_alert(
            patient.preferred_name,
            "ORANGE" if session["risk_score"] < 50 else "RED",
            session["risk_score"],
            list(set(session["signals"]))
        )


def setup_bot():
    """Setup and return the bot application (for deployment)."""
    global scheduler
    
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set!")
    
    # Only create scheduler if not already set (by bot_server.py)
    if scheduler is None:
        scheduler = CheckinScheduler()
        scheduler.load_patients()
    
    logger.info("=" * 60)
    logger.info("🏥 PROJECT IC - Telegram Voice Bot")
    logger.info("=" * 60)
    logger.info(f"Bot Token: {BOT_TOKEN[:20]}...")
    logger.info(f"Case Worker ID: {CASE_WORKER_CHAT_ID}")
    logger.info(f"MERaLiON API: {MERALION_API_URL}")
    logger.info(f"Registered Patients: {len(scheduler.patients)}")
    
    # Log medication info
    if scheduler.medication_manager:
        med_count = sum(len(meds) for meds in scheduler.medication_manager.medications.values())
        logger.info(f"Medication Reminders: {med_count} medications")
    
    logger.info("=" * 60)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("end", end_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Medication commands
    application.add_handler(CommandHandler("addmed", addmed_command))
    application.add_handler(CommandHandler("delmed", delmed_command))
    application.add_handler(CommandHandler("listmed", listmed_command))
    application.add_handler(CommandHandler("adherence", adherence_command))
    
    # Medication callback handler (for confirmation buttons)
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(addmed_callback, pattern="^addmed_"))
    application.add_handler(CallbackQueryHandler(delmed_callback, pattern="^delmed_"))
    
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    return application


def main():
    """Start the bot."""
    global scheduler
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        print("Get it from @BotFather on Telegram")
        sys.exit(1)
    
    # Initialize scheduler and load patients
    scheduler = CheckinScheduler()
    scheduler.load_patients()
    
    print("=" * 60)
    print("🏥 PROJECT IC - Telegram Voice Bot")
    print("=" * 60)
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Case Worker ID: {CASE_WORKER_CHAT_ID}")
    print(f"MERaLiON API: {MERALION_API_URL}")
    print(f"Voice Output: {'✅ Enabled' if VOICE_OUTPUT_ENABLED else '❌ Disabled'}")
    print("=" * 60)
    print("\n🗣️ Voice Features:")
    print("  • Voice Input: Patient speaks → Bot listens")
    print("  • Voice Output: Bot speaks back naturally")
    print("  • Singlish Support: Natural local language")
    print("=" * 60)
    print("\n📅 Daily Check-ins:")
    print("  • Morning: 8:00 AM 🌅")
    print("  • Afternoon: 2:00 PM 🌤️")
    print(f"  • Registered Patients: {len(scheduler.patients)}")
    print("=" * 60)
    print("\n💊 Medication Commands (Case Workers):")
    print("  • /addmed <patient_id> <name> <dosage> <times>")
    print("  • /listmed [patient_id]")
    print("  • /adherence <patient_id>")
    print("=" * 60)
    print("\n🗣️ Wake Words (start check-in by saying):")
    print("  • 'Hello Aescul Helper'")
    print("  • 'Hello AesculAI'")
    print("  • 'Hi Aescul'")
    print("=" * 60)
    print("\nBot is running! Send a message to @AesculAI_helper_bot")
    print("=" * 60)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("end", end_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Medication commands
    application.add_handler(CommandHandler("addmed", addmed_command))
    application.add_handler(CommandHandler("delmed", delmed_command))
    application.add_handler(CommandHandler("listmed", listmed_command))
    application.add_handler(CommandHandler("adherence", adherence_command))
    
    # Medication callback handler (for confirmation buttons)
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(addmed_callback, pattern="^addmed_"))
    application.add_handler(CallbackQueryHandler(delmed_callback, pattern="^delmed_"))
    
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
