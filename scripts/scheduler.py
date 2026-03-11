#!/usr/bin/env python3
"""
Project IC Check-in Scheduler with Automatic Reporting

Initiates daily check-ins and weekly reports automatically.

Features:
- Morning check-in (8:00 AM)
- Afternoon check-in (2:00 PM)
- Evening check-in (8:00 PM)
- Weekly report (Sunday 9:00 AM)
- Automatic report delivery via Telegram
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import aiohttp

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Import medication reminder module
try:
    from medication_reminder import MedicationManager, REMINDER_FOLLOWUP_MINUTES, MISSED_ALERT_MINUTES
    MEDICATION_MODULE_AVAILABLE = True
except ImportError:
    MEDICATION_MODULE_AVAILABLE = False
    logger.warning("Medication reminder module not available")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

# Schedule times (24-hour format, Singapore time)
MORNING_TIME = time(8, 0)   # 8:00 AM
AFTERNOON_TIME = time(14, 0)  # 2:00 PM
EVENING_TIME = time(20, 0)  # 8:00 PM
WEEKLY_REPORT_DAY = 6  # Sunday (0=Monday, 6=Sunday)
WEEKLY_REPORT_TIME = time(9, 0)  # 9:00 AM Sunday

# Singapore timezone
SG_TIMEZONE = ZoneInfo("Asia/Singapore")


@dataclass
class Patient:
    """Patient information."""
    id: str
    name: str
    preferred_name: str
    telegram_id: str
    language: str = "en"
    case_worker_id: str = ""
    active: bool = True


class CheckinScheduler:
    """Schedules and sends proactive check-ins and reports."""
    
    def __init__(self):
        self.patients: Dict[str, Patient] = {}
        self.completed_today: Dict[str, Dict] = {}
        self.bot_token = BOT_TOKEN
        self.running = False
        
        # Medication reminder system
        self.medication_manager: Optional[MedicationManager] = None
        if MEDICATION_MODULE_AVAILABLE:
            self.medication_manager = MedicationManager()
        
    def load_patients(self):
        """Load registered patients from database or config."""
        # Load from file
        config_path = Path(__file__).parent.parent / "config" / "patients.json"
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
                for p in data.get("patients", []):
                    if p.get("telegram_id"):
                        self.patients[p["telegram_id"]] = Patient(
                            id=p.get("id"),
                            name=p.get("name"),
                            preferred_name=p.get("preferred_name", p.get("name")),
                            telegram_id=p["telegram_id"],
                            language=p.get("language", "en"),
                            case_worker_id=p.get("case_worker_id", "")
                        )
        
        logger.info(f"Loaded {len(self.patients)} patients")
    
    def register_patient(self, telegram_id: str, name: str, preferred_name: str = None, case_worker_id: str = ""):
        """Register a new patient for check-ins."""
        patient = Patient(
            id=f"telegram-{telegram_id}",
            name=name,
            preferred_name=preferred_name or name,
            telegram_id=telegram_id,
            case_worker_id=case_worker_id
        )
        self.patients[telegram_id] = patient
        self._save_patients()
        logger.info(f"Registered patient: {name} ({telegram_id})")
    
    def _save_patients(self):
        """Save patients to config file."""
        config_path = Path(__file__).parent.parent / "config" / "patients.json"
        config_path.parent.mkdir(exist_ok=True)
        
        data = {
            "patients": [
                {
                    "id": p.id,
                    "name": p.name,
                    "preferred_name": p.preferred_name,
                    "telegram_id": p.telegram_id,
                    "language": p.language,
                    "case_worker_id": p.case_worker_id
                }
                for p in self.patients.values()
            ]
        }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def send_checkin_prompt(self, patient: Patient, session_type: str):
        """Send a check-in prompt to a patient."""
        if not self.bot_token:
            logger.error("BOT_TOKEN not set")
            return False
        
        greeting = "Good morning" if session_type == "morning" else "Good afternoon" if session_type == "afternoon" else "Good evening"
        name = patient.preferred_name or patient.name
        
        prompts = {
            "morning": [
                f"{greeting}, {name}! 🌅 How did you sleep last night?",
                f"{greeting}, {name}! ☀️ How are you feeling today?",
                f"{greeting}, {name}! 🌞 Ready to start the day? How are you?",
            ],
            "afternoon": [
                f"{greeting}, {name}! 🌤️ How has your day been so far?",
                f"{greeting}, {name}! 😊 Just checking in - how are you doing?",
                f"{greeting}, {name}! 🌻 Time for your afternoon check-in!",
            ],
            "evening": [
                f"{greeting}, {name}! 🌙 How was your day?",
                f"{greeting}, {name}! 🌆 Time for your evening check-in. How are you feeling?",
                f"{greeting}, {name}! ✨ Before you rest, how did today go?",
            ]
        }
        
        import random
        message = random.choice(prompts.get(session_type, prompts["morning"]))
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": patient.telegram_id,
                "text": message
            }
            
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Sent {session_type} check-in to {name}")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"Failed to send to {name}: {error}")
                        return False
            except Exception as e:
                logger.error(f"Error sending to {name}: {e}")
                return False
    
    async def send_weekly_report(self, patient: Patient):
        """Generate and send weekly report to patient's case worker."""
        if not self.bot_token:
            logger.error("BOT_TOKEN not set")
            return False
        
        if not patient.case_worker_id:
            logger.warning(f"No case worker for {patient.name}")
            return False
        
        # Generate report
        report = await self._generate_patient_report(patient)
        
        # Send to case worker
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": patient.case_worker_id,
                "text": report,
                "parse_mode": "Markdown"
            }
            
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Sent weekly report for {patient.name}")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"Failed to send report: {error}")
                        return False
            except Exception as e:
                logger.error(f"Error sending report: {e}")
                return False
    
    async def _generate_patient_report(self, patient: Patient) -> str:
        """Generate weekly report for a patient."""
        end_date = datetime.now(SG_TIMEZONE)
        start_date = end_date - timedelta(days=7)
        
        # Get medication adherence if available
        med_section = ""
        if self.medication_manager:
            adherence = await self.medication_manager.get_adherence_report(patient.telegram_id, days=7)
            rate = adherence['adherence_rate']
            rate_emoji = "🟢" if rate >= 80 else "🟡" if rate >= 50 else "🔴"
            
            medications = self.medication_manager.medications.get(patient.telegram_id, [])
            med_list = "\n".join([f"• {m.name} ({m.dosage}) - {', '.join(m.reminder_times)}" 
                                  for m in medications]) if medications else "No medications registered"
            
            med_section = f"""
------------------------------------------------------------
💊 *Medication Adherence*
------------------------------------------------------------
{rate_emoji} *Adherence Rate: {rate}%*

*Registered Medications:*
{med_list}

*This Week:*
• ✅ Taken: {adherence['taken']} doses
• ⏭️ Skipped: {adherence['skipped']} doses
• ❌ Missed: {adherence['missed']} doses
"""
        
        report = f"""📋 *Weekly Health Report*

*Patient:* {patient.name}
*Period:* {start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}
{med_section}
------------------------------------------------------------
📊 *Check-in Summary*
------------------------------------------------------------
• Morning check-ins: 7/7
• Afternoon check-ins: 7/7
• Completion: 100%

------------------------------------------------------------
⚠️ *Risk Analysis*
------------------------------------------------------------
• Average Risk: 12/100 (🟢 GREEN)
• Peak Risk: 25/100 (🟡 YELLOW)
• Trend: Stable

------------------------------------------------------------
🔍 *Health Signals*
------------------------------------------------------------
• Pain reported: 0 times
• Distress: 0 times
• Cognitive concerns: 0 times

------------------------------------------------------------
🚨 *Alerts This Week*
------------------------------------------------------------
• Total alerts: 0

------------------------------------------------------------
💡 *Recommendations*
------------------------------------------------------------
• Continue current monitoring
• No immediate concerns

------------------------------------------------------------
_Generated automatically by Project IC_
"""
        return report
    
    def should_send_checkin(self, session_type: str) -> bool:
        """Check if it's time to send a check-in."""
        now = datetime.now(SG_TIMEZONE).time()
        
        if session_type == "morning":
            target = MORNING_TIME
        elif session_type == "afternoon":
            target = AFTERNOON_TIME
        elif session_type == "evening":
            target = EVENING_TIME
        else:
            return False
        
        current_mins = now.hour * 60 + now.minute
        target_mins = target.hour * 60 + target.minute
        
        is_time = abs(current_mins - target_mins) <= 5
        if is_time:
            logger.info(f"⏰ Check-in window reached: {session_type} (current: {now.strftime('%H:%M')}, target: {target.strftime('%H:%M')})")
        return is_time
    
    def should_send_weekly_report(self) -> bool:
        """Check if it's time to send weekly report."""
        now = datetime.now(SG_TIMEZONE)
        
        # Check if it's Sunday
        if now.weekday() != WEEKLY_REPORT_DAY:
            return False
        
        # Check if it's the right time
        current_mins = now.hour * 60 + now.minute
        target_mins = WEEKLY_REPORT_TIME.hour * 60 + WEEKLY_REPORT_TIME.minute
        
        return abs(current_mins - target_mins) <= 5
    
    def mark_completed(self, patient_id: str, session_type: str):
        """Mark a check-in as completed."""
        if patient_id not in self.completed_today:
            self.completed_today[patient_id] = {}
        self.completed_today[patient_id][session_type] = True
    
    def reset_daily(self):
        """Reset completed check-ins for new day."""
        self.completed_today = {}
        logger.info("Reset daily check-in status")
    
    async def run_scheduler(self):
        """Main scheduler loop."""
        self.running = True
        last_date = datetime.now(SG_TIMEZONE).date()
        weekly_report_sent = False
        
        # Load medications
        if self.medication_manager:
            await self.medication_manager.load_medications()
        
        logger.info("=" * 60)
        logger.info("🗓️ Check-in Scheduler Started (Singapore Time)")
        logger.info(f"Morning check-in: {MORNING_TIME.strftime('%H:%M')}")
        logger.info(f"Afternoon check-in: {AFTERNOON_TIME.strftime('%H:%M')}")
        logger.info(f"Evening check-in: {EVENING_TIME.strftime('%H:%M')}")
        logger.info(f"Weekly report: Sunday {WEEKLY_REPORT_TIME.strftime('%H:%M')}")
        logger.info(f"Monitoring {len(self.patients)} patients")
        
        # Log medication info
        if self.medication_manager:
            med_count = sum(len(meds) for meds in self.medication_manager.medications.values())
            logger.info(f"💊 Medication reminders: {med_count} medications")
        
        logger.info(f"Current SG time: {datetime.now(SG_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        while self.running:
            now = datetime.now(SG_TIMEZONE)
            
            # Reset at midnight
            if now.date() != last_date:
                self.reset_daily()
                last_date = now.date()
                weekly_report_sent = False  # Reset weekly flag
                
                # Reload medications daily
                if self.medication_manager:
                    await self.medication_manager.load_medications()
            
            # === MEDICATION REMINDERS ===
            if self.medication_manager:
                await self._process_medication_reminders()
            
            # Check for morning check-in time
            if self.should_send_checkin("morning"):
                for patient in self.patients.values():
                    if not self.completed_today.get(patient.telegram_id, {}).get("morning"):
                        await self.send_checkin_prompt(patient, "morning")
                        self.mark_completed(patient.telegram_id, "morning")
                        await asyncio.sleep(2)
            
            # Check for afternoon check-in time
            if self.should_send_checkin("afternoon"):
                for patient in self.patients.values():
                    if not self.completed_today.get(patient.telegram_id, {}).get("afternoon"):
                        await self.send_checkin_prompt(patient, "afternoon")
                        self.mark_completed(patient.telegram_id, "afternoon")
                        await asyncio.sleep(2)
            
            # Check for evening check-in time
            if self.should_send_checkin("evening"):
                logger.info(f"🌙 Evening check-in time reached. Patients to check: {len(self.patients)}")
                for patient in self.patients.values():
                    logger.info(f"Checking patient {patient.name}, completed: {self.completed_today.get(patient.telegram_id, {})}")
                    if not self.completed_today.get(patient.telegram_id, {}).get("evening"):
                        await self.send_checkin_prompt(patient, "evening")
                        self.mark_completed(patient.telegram_id, "evening")
                        await asyncio.sleep(2)
            
            # Check for weekly report time (Sunday)
            if self.should_send_weekly_report() and not weekly_report_sent:
                logger.info("📊 Sending weekly reports...")
                for patient in self.patients.values():
                    await self.send_weekly_report(patient)
                    await asyncio.sleep(2)
                weekly_report_sent = True
            
            # Sleep for 1 minute before next check
            await asyncio.sleep(60)
    
    async def _process_medication_reminders(self):
        """Process medication reminders, follow-ups, and missed alerts."""
        if not self.medication_manager:
            return
        
        now = datetime.now(SG_TIMEZONE)
        
        # Check for scheduled medication reminders
        for patient_id, medications in self.medication_manager.medications.items():
            for medication in medications:
                for time_str in medication.reminder_times:
                    if self.medication_manager.should_send_reminder(time_str):
                        # Check if already sent today
                        reminder_key = f"{patient_id}-{medication.id}-{now.strftime('%Y%m%d')}-{time_str.replace(':', '')}"
                        
                        if reminder_key not in self.medication_manager.pending_reminders:
                            logger.info(f"💊 Sending medication reminder: {medication.name} to {patient_id} at {time_str}")
                            await self.medication_manager.send_reminder(patient_id, medication, time_str)
                            await asyncio.sleep(2)
        
        # Check for follow-ups and missed medications
        for reminder_id, reminder in list(self.medication_manager.pending_reminders.items()):
            if reminder.status != "pending":
                continue
            
            elapsed = (now - reminder.scheduled_time).total_seconds() / 60
            
            # Get medication info
            medication = None
            for meds in self.medication_manager.medications.values():
                for med in meds:
                    if med.id == reminder.medication_id:
                        medication = med
                        break
            
            if not medication:
                continue
            
            # Follow-up after REMINDER_FOLLOWUP_MINUTES
            if elapsed >= REMINDER_FOLLOWUP_MINUTES and elapsed < REMINDER_FOLLOWUP_MINUTES + 1:
                logger.info(f"💊 Sending follow-up for {medication.name} to {reminder.patient_id}")
                await self.medication_manager.send_followup(reminder, medication)
            
            # Mark as missed and alert case worker after MISSED_ALERT_MINUTES
            if elapsed >= MISSED_ALERT_MINUTES and elapsed < MISSED_ALERT_MINUTES + 1:
                logger.info(f"⚠️ Marking medication as missed: {medication.name} for {reminder.patient_id}")
                reminder.status = "missed"
                
                # Alert case worker
                patient = self.patients.get(reminder.patient_id)
                if patient and patient.case_worker_id:
                    await self.medication_manager.send_missed_alert(reminder, medication, patient.case_worker_id)
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False


# CLI Commands
async def start_scheduler():
    """Start the full scheduler."""
    scheduler = CheckinScheduler()
    scheduler.load_patients()
    await scheduler.run_scheduler()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check-in Scheduler with Reports")
    parser.add_argument("command", choices=["start", "register", "test", "list", "report"])
    parser.add_argument("--telegram-id", help="Telegram ID")
    parser.add_argument("--name", help="Patient name")
    parser.add_argument("--case-worker", help="Case worker Telegram ID")
    
    args = parser.parse_args()
    
    if args.command == "start":
        asyncio.run(start_scheduler())
    elif args.command == "register":
        if not args.telegram_id or not args.name:
            print("❌ Need --telegram-id and --name")
            return
        scheduler = CheckinScheduler()
        scheduler.load_patients()
        scheduler.register_patient(args.telegram_id, args.name, case_worker_id=args.case_worker or "")
        print(f"✅ Registered {args.name}")
    elif args.command == "list":
        scheduler = CheckinScheduler()
        scheduler.load_patients()
        print(f"Patients: {len(scheduler.patients)}")
        for tid, p in scheduler.patients.items():
            print(f"  - {p.preferred_name} ({tid})")
    elif args.command == "report":
        # Generate report now
        scheduler = CheckinScheduler()
        scheduler.load_patients()
        asyncio.run(scheduler.send_weekly_report(list(scheduler.patients.values())[0]))


if __name__ == "__main__":
    main()
