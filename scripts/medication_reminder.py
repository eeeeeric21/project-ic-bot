#!/usr/bin/env python3
"""
Project IC Medication Reminder System

Handles medication scheduling, reminders, and tracking.

Features:
- Schedule medication reminders at specific times
- Track medication adherence (taken/skipped/missed)
- Escalate to case worker if medication is missed
- Generate adherence reports
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

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

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

# Singapore timezone
SG_TIMEZONE = ZoneInfo("Asia/Singapore")

# Reminder settings
REMINDER_FOLLOWUP_MINUTES = 30  # Follow up after 30 mins if no response
MISSED_ALERT_MINUTES = 60       # Alert case worker after 60 mins


@dataclass
class Medication:
    """Medication information."""
    id: str
    patient_id: str
    name: str
    dosage: str
    instructions: str
    reminder_times: List[str]  # ["08:00", "14:00"]
    active: bool = True


@dataclass
class MedicationReminder:
    """Medication reminder tracking."""
    id: str
    medication_id: str
    patient_id: str
    scheduled_time: datetime
    status: str = "pending"  # pending, taken, skipped, missed


class MedicationManager:
    """Manages medication reminders and tracking."""
    
    def __init__(self):
        self.medications: Dict[str, List[Medication]] = {}  # patient_id -> medications
        self.pending_reminders: Dict[str, MedicationReminder] = {}  # reminder_id -> reminder
        self.bot_token = BOT_TOKEN
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        
    async def load_medications(self):
        """Load medications from Supabase (primary) or file (fallback)."""
        if self.supabase_url and self.supabase_key:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.supabase_url}/rest/v1/medications?active=eq.true&select=*"
                    headers = {
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self.medications = {}
                            
                            for med in data:
                                patient_id = med["patient_id"]
                                if patient_id not in self.medications:
                                    self.medications[patient_id] = []
                                
                                self.medications[patient_id].append(Medication(
                                    id=med["id"],
                                    patient_id=patient_id,
                                    name=med["name"],
                                    dosage=med.get("dosage", ""),
                                    instructions=med.get("instructions", ""),
                                    reminder_times=med.get("reminder_times", [])
                                ))
                            
                            total = sum(len(meds) for meds in self.medications.values())
                            logger.info(f"✅ Loaded {total} medications from Supabase for {len(self.medications)} patients")
                            return
                        else:
                            error = await resp.text()
                            logger.error(f"Supabase error: {resp.status} - {error}")
            except Exception as e:
                logger.error(f"Error loading from Supabase: {e}")
        
        # Fallback to file
        logger.info("Falling back to file storage for medications")
        self._load_medications_from_file()
    
    def _load_medications_from_file(self):
        """Fallback: Load medications from local file."""
        config_path = Path(__file__).parent.parent / "config" / "medications.json"
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
                self.medications = {}
                
                for med in data.get("medications", []):
                    patient_id = med["patient_id"]
                    if patient_id not in self.medications:
                        self.medications[patient_id] = []
                    
                    self.medications[patient_id].append(Medication(
                        id=med.get("id", f"med-{len(self.medications)}"),
                        patient_id=patient_id,
                        name=med["name"],
                        dosage=med.get("dosage", ""),
                        instructions=med.get("instructions", ""),
                        reminder_times=med.get("reminder_times", [])
                    ))
            
            total = sum(len(meds) for meds in self.medications.values())
            logger.info(f"Loaded {total} medications from file")
    
    def add_medication(self, patient_id: str, name: str, dosage: str, 
                       instructions: str, reminder_times: List[str]) -> Medication:
        """Add a new medication for a patient (saves to both memory and file)."""
        med_id = f"med-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        medication = Medication(
            id=med_id,
            patient_id=patient_id,
            name=name,
            dosage=dosage,
            instructions=instructions,
            reminder_times=reminder_times
        )
        
        if patient_id not in self.medications:
            self.medications[patient_id] = []
        
        self.medications[patient_id].append(medication)
        
        # Save to file as backup (will be replaced by Supabase save in async version)
        self._save_medications_to_file()
        
        logger.info(f"Added medication {name} for patient {patient_id}")
        return medication
    
    async def add_medication_async(self, patient_id: str, name: str, dosage: str,
                                    instructions: str, reminder_times: List[str],
                                    created_by: str = None) -> Medication:
        """Add a new medication and save to Supabase."""
        if self.supabase_url and self.supabase_key:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.supabase_url}/rest/v1/medications"
                    headers = {
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    }
                    
                    payload = {
                        "patient_id": patient_id,
                        "name": name,
                        "dosage": dosage,
                        "instructions": instructions,
                        "reminder_times": reminder_times,
                        "created_by": created_by,
                        "active": True
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status == 201:
                            data = await resp.json()
                            med_data = data[0] if isinstance(data, list) else data
                            
                            medication = Medication(
                                id=med_data["id"],
                                patient_id=patient_id,
                                name=name,
                                dosage=dosage,
                                instructions=instructions,
                                reminder_times=reminder_times
                            )
                            
                            if patient_id not in self.medications:
                                self.medications[patient_id] = []
                            self.medications[patient_id].append(medication)
                            
                            logger.info(f"✅ Saved medication {name} to Supabase for {patient_id}")
                            return medication
                        else:
                            error = await resp.text()
                            logger.error(f"Failed to save to Supabase: {resp.status} - {error}")
            except Exception as e:
                logger.error(f"Error saving to Supabase: {e}")
        
        # Fallback to local
        return self.add_medication(patient_id, name, dosage, instructions, reminder_times)
    
    async def delete_medication_async(self, patient_id: str, medication_id: str) -> bool:
        """Delete a medication from Supabase."""
        if self.supabase_url and self.supabase_key:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.supabase_url}/rest/v1/medications?id=eq.{medication_id}"
                    headers = {
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.delete(url, headers=headers) as resp:
                        if resp.status == 204:
                            # Remove from memory
                            if patient_id in self.medications:
                                self.medications[patient_id] = [
                                    m for m in self.medications[patient_id] if m.id != medication_id
                                ]
                            logger.info(f"✅ Deleted medication {medication_id} from Supabase")
                            return True
                        else:
                            error = await resp.text()
                            logger.error(f"Failed to delete from Supabase: {resp.status} - {error}")
                            return False
            except Exception as e:
                logger.error(f"Error deleting from Supabase: {e}")
                return False
        
        # Fallback: remove from memory only
        if patient_id in self.medications:
            self.medications[patient_id] = [
                m for m in self.medications[patient_id] if m.id != medication_id
            ]
        return True
    
    def _save_medications_to_file(self):
        """Save medications to local file."""
        config_path = Path(__file__).parent.parent / "config" / "medications.json"
        config_path.parent.mkdir(exist_ok=True)
        
        all_meds = []
        for meds in self.medications.values():
            for med in meds:
                all_meds.append({
                    "id": med.id,
                    "patient_id": med.patient_id,
                    "name": med.name,
                    "dosage": med.dosage,
                    "instructions": med.instructions,
                    "reminder_times": med.reminder_times,
                    "active": med.active
                })
        
        with open(config_path, 'w') as f:
            json.dump({"medications": all_meds}, f, indent=2)
    
    async def send_reminder(self, patient_id: str, medications: List[Medication], time_str: str):
        """Send a medication reminder to a patient with inline buttons."""
        if not self.bot_token:
            logger.error("BOT_TOKEN not set")
            return False
        
        # Build message for multiple medications
        time_display = self._format_time(time_str)
        message = f"⏰ *{time_display} — Time for your medicine:*\n\n"
        
        for med in medications:
            message += f"💊 *{med.name}*"
            if med.dosage:
                message += f" — {med.dosage}"
            message += "\n"
            if med.instructions:
                message += f"   _{med.instructions}_\n"
        
        # Build inline keyboard with individual medication buttons
        inline_keyboard = []
        date_str = datetime.now(SG_TIMEZONE).strftime('%Y%m%d')
        time_str_safe = time_str.replace(':', '')
        
        for med in medications:
            callback_taken = f"med_taken:{patient_id}:{med.id}:{date_str}:{time_str_safe}"
            callback_skip = f"med_skip:{patient_id}:{med.id}:{date_str}:{time_str_safe}"
            
            inline_keyboard.append([
                {"text": f"✓ Taken {med.name}", "callback_data": callback_taken},
                {"text": f"⏭ Skip {med.name}", "callback_data": callback_skip}
            ])
        
        # Add "Taken All" button if multiple medications
        if len(medications) > 1:
            callback_all = f"med_taken_all:{patient_id}:{date_str}:{time_str_safe}"
            inline_keyboard.append([
                {"text": f"✅ Taken All ({len(medications)} meds)", "callback_data": callback_all}
            ])
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": patient_id,
                "text": message,
                "parse_mode": "Markdown",
                "reply_markup": {"inline_keyboard": inline_keyboard}
            }
            
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        message_id = data.get("result", {}).get("message_id")
                        
                        # Track reminders for each medication
                        for med in medications:
                            reminder_id = f"{patient_id}-{med.id}-{date_str}-{time_str_safe}"
                            self.pending_reminders[reminder_id] = MedicationReminder(
                                id=reminder_id,
                                medication_id=med.id,
                                patient_id=patient_id,
                                scheduled_time=datetime.now(SG_TIMEZONE)
                            )
                        
                        logger.info(f"✅ Sent medication reminder to {patient_id}: {len(medications)} medications")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"Failed to send reminder: {error}")
                        return False
            except Exception as e:
                logger.error(f"Error sending reminder: {e}")
                return False
    
    def _format_time(self, time_str: str) -> str:
        """Format time for display (08:00 → 8:00 AM)."""
        try:
            hour, minute = map(int, time_str.split(':'))
            period = "PM" if hour >= 12 else "AM"
            display_hour = hour % 12 or 12
            return f"{display_hour}:{minute:02d} {period}"
        except:
            return time_str
    
    async def send_followup(self, reminder: MedicationReminder, medication: Medication):
        """Send a follow-up reminder if no response."""
        if not self.bot_token:
            return False
        
        message = f"""💊 *Gentle Reminder*

Did you take your {medication.name}?

Reply:
• "taken" - if you've taken it
• "skip" - if you're skipping it"""
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": reminder.patient_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Sent follow-up to {reminder.patient_id}")
                        return True
                    return False
            except Exception as e:
                logger.error(f"Error sending follow-up: {e}")
                return False
    
    async def send_missed_alert(self, reminder: MedicationReminder, medication: Medication, 
                                 case_worker_id: str):
        """Alert case worker about missed medication."""
        if not self.bot_token:
            return False
        
        scheduled = reminder.scheduled_time.strftime('%H:%M')
        
        message = f"""⚠️ *Missed Medication Alert*

*Patient:* {reminder.patient_id}
*Medication:* {medication.name} ({medication.dosage})
*Scheduled:* {scheduled}
*Status:* No response after {MISSED_ALERT_MINUTES} minutes

Please follow up with the patient.
"""
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": case_worker_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Sent missed alert to case worker {case_worker_id}")
                        return True
                    return False
            except Exception as e:
                logger.error(f"Error sending alert: {e}")
                return False
    
    def mark_taken(self, patient_id: str, reminder_id: str = None):
        """Mark a medication as taken."""
        # Find the most recent pending reminder for this patient
        for rid, reminder in self.pending_reminders.items():
            if reminder.patient_id == patient_id and reminder.status == "pending":
                reminder.status = "taken"
                logger.info(f"Marked medication as taken: {rid}")
                return True
        return False
    
    def mark_skipped(self, patient_id: str, reason: str = "", reminder_id: str = None):
        """Mark a medication as skipped."""
        for rid, reminder in self.pending_reminders.items():
            if reminder.patient_id == patient_id and reminder.status == "pending":
                reminder.status = "skipped"
                logger.info(f"Marked medication as skipped: {rid}")
                return True
        return False
    
    def should_send_reminder(self, time_str: str) -> bool:
        """Check if current time matches a reminder time (within 5 min window)."""
        now = datetime.now(SG_TIMEZONE)
        current_mins = now.hour * 60 + now.minute
        
        try:
            hour, minute = map(int, time_str.split(':'))
            target_mins = hour * 60 + minute
            
            # 5 minute window
            return abs(current_mins - target_mins) <= 5
        except:
            return False
    
    def get_medication_for_reminder(self, reminder_id: str) -> Optional[Medication]:
        """Get medication by ID."""
        for meds in self.medications.values():
            for med in meds:
                if med.id == reminder_id.split('-')[1] if '-' in reminder_id else reminder_id:
                    return med
        return None
    
    async def get_adherence_report(self, patient_id: str, days: int = 7) -> Dict:
        """Generate medication adherence report for a patient."""
        # For now, use local tracking
        # In production, fetch from database
        
        taken = 0
        skipped = 0
        missed = 0
        
        # Per-medication tracking
        med_stats: Dict[str, Dict] = {}
        
        for reminder in self.pending_reminders.values():
            if reminder.patient_id == patient_id:
                # Get medication name
                med_name = "Unknown"
                for meds in self.medications.values():
                    for med in meds:
                        if med.id == reminder.medication_id:
                            med_name = f"{med.name} ({med.dosage})" if med.dosage else med.name
                            break
                
                # Initialize per-med stats
                if med_name not in med_stats:
                    med_stats[med_name] = {"taken": 0, "skipped": 0, "missed": 0}
                
                if reminder.status == "taken":
                    taken += 1
                    med_stats[med_name]["taken"] += 1
                elif reminder.status == "skipped":
                    skipped += 1
                    med_stats[med_name]["skipped"] += 1
                elif reminder.status == "missed":
                    missed += 1
                    med_stats[med_name]["missed"] += 1
        
        total = taken + skipped + missed
        adherence_rate = (taken / total * 100) if total > 0 else 0
        
        return {
            "patient_id": patient_id,
            "period_days": days,
            "total_doses": total,
            "taken": taken,
            "skipped": skipped,
            "missed": missed,
            "adherence_rate": round(adherence_rate, 1),
            "by_medication": med_stats
        }

    # ============================================
    # INLINE BUTTON CALLBACK HANDLERS
    # ============================================
    
    # Skip reason labels
    SKIP_REASONS = {
        "already_took": "✅ Already took it",
        "side_effects": "⚠️ Side effects",
        "doctor_paused": "👨‍⚕️ Doctor said pause",
        "ran_out": "💊 Ran out",
        "dont_need": "❌ Don't need it",
        "no_reason": "🤷 No reason",
        "dismissed": "Dismiss",
    }
    
    # Reasons that trigger caregiver alerts
    ALERT_REASONS = ["side_effects", "ran_out"]
    
    # Reasons that should mark as taken instead
    TAKEN_REASONS = ["already_took"]
    
    async def handle_callback(self, callback_data: str, chat_id: int, message_id: int = None) -> Dict:
        """
        Handle inline button callbacks for medication reminders.
        
        Args:
            callback_data: The callback data from the button
            chat_id: Telegram chat ID
            message_id: Optional message ID for editing
        
        Returns:
            Dict with 'success', 'message', and 'alert_needed' keys
        """
        try:
            parts = callback_data.split(":")
            action = parts[0]
            
            if action == "med_taken" and len(parts) >= 5:
                # med_taken:patient_id:med_id:date:time
                patient_id = parts[1]
                med_id = parts[2]
                
                result = self.mark_taken_by_id(patient_id, med_id)
                
                if result:
                    med_name = self._get_med_name(med_id)
                    return {
                        "success": True,
                        "message": f"✅ *Logged:* {med_name} taken at {self._current_time()}",
                        "alert_needed": False
                    }
                else:
                    return {"success": False, "message": "⚠️ Could not log medication."}
            
            elif action == "med_skip" and len(parts) >= 5:
                # med_skip:patient_id:med_id:date:time
                patient_id = parts[1]
                med_id = parts[2]
                
                # Send skip reason buttons
                keyboard = self._build_skip_reason_keyboard(patient_id, med_id)
                med_name = self._get_med_name(med_id)
                
                return {
                    "success": True,
                    "message": f"⏭ *Skipped:* {med_name}\n\nMay I ask why? (This helps your care team)",
                    "keyboard": keyboard,
                    "alert_needed": False
                }
            
            elif action == "med_reason" and len(parts) >= 4:
                # med_reason:reason:patient_id:med_id (date/time optional)
                reason = parts[1]
                patient_id = parts[2]
                med_id = parts[3]
                
                # Mark as taken or skipped based on reason
                if reason in self.TAKEN_REASONS:
                    self.mark_taken_by_id(patient_id, med_id, reason=reason)
                    final_action = "taken"
                else:
                    self.mark_skipped_by_id(patient_id, med_id, reason=reason)
                    final_action = "skipped"
                
                med_name = self._get_med_name(med_id)
                
                # Build response message
                if reason in self.TAKEN_REASONS:
                    response_msg = f"✅ Got it, marked {med_name} as taken."
                elif reason in self.ALERT_REASONS:
                    reason_text = "side effects" if reason == "side_effects" else "refill needed"
                    response_msg = f"📝 Noted. I'll let your caregiver know about the {reason_text}."
                elif reason == "doctor_paused":
                    response_msg = f"✅ Understood. We'll note that the doctor paused {med_name}."
                else:
                    response_msg = "✅ Okay, logged as skipped."
                
                return {
                    "success": True,
                    "message": response_msg,
                    "alert_needed": reason in self.ALERT_REASONS,
                    "alert_reason": reason,
                    "patient_id": patient_id,
                    "medication_name": med_name
                }
            
            elif action == "med_taken_all" and len(parts) >= 4:
                # med_taken_all:patient_id:date:time
                patient_id = parts[1]
                
                count = self.mark_all_taken(patient_id)
                
                return {
                    "success": True,
                    "message": f"✅ All medications logged as taken at {self._current_time()}",
                    "alert_needed": False
                }
            
            else:
                return {"success": False, "message": "⚠️ Invalid action."}
                
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            return {"success": False, "message": "⚠️ An error occurred."}
    
    def _build_skip_reason_keyboard(self, patient_id: str, med_id: str) -> List[List[Dict]]:
        """Build inline keyboard with skip reason buttons."""
        keyboard = []
        for code, label in self.SKIP_REASONS.items():
            keyboard.append([{
                "text": label,
                "callback_data": f"med_reason:{code}:{patient_id}:{med_id}"
            }])
        return keyboard
    
    def mark_taken_by_id(self, patient_id: str, med_id: str, reason: str = None) -> bool:
        """Mark a specific medication as taken."""
        for rid, reminder in self.pending_reminders.items():
            if (reminder.patient_id == patient_id and 
                med_id in rid and 
                reminder.status == "pending"):
                reminder.status = "taken"
                logger.info(f"Marked medication as taken: {rid}")
                return True
        return False
    
    def mark_skipped_by_id(self, patient_id: str, med_id: str, reason: str = None) -> bool:
        """Mark a specific medication as skipped with reason."""
        for rid, reminder in self.pending_reminders.items():
            if (reminder.patient_id == patient_id and 
                med_id in rid and 
                reminder.status == "pending"):
                reminder.status = "skipped"
                # Store skip reason (you could add a field to MedicationReminder)
                logger.info(f"Marked medication as skipped: {rid}, reason: {reason}")
                return True
        return False
    
    def mark_all_taken(self, patient_id: str) -> int:
        """Mark all pending medications as taken for a patient."""
        count = 0
        for rid, reminder in self.pending_reminders.items():
            if reminder.patient_id == patient_id and reminder.status == "pending":
                reminder.status = "taken"
                count += 1
        logger.info(f"Marked {count} medications as taken for {patient_id}")
        return count
    
    def _get_med_name(self, med_id: str) -> str:
        """Get medication name by ID."""
        for meds in self.medications.values():
            for med in meds:
                if med.id == med_id:
                    name = med.name
                    if med.dosage:
                        name += f" ({med.dosage})"
                    return name
        return "Medication"
    
    def _current_time(self) -> str:
        """Get current time string."""
        return datetime.now(SG_TIMEZONE).strftime('%-I:%M %p')


# CLI Commands
async def main():
    """Test the medication manager."""
    manager = MedicationManager()
    await manager.load_medications()
    
    print(f"\n💊 Loaded medications:")
    for patient_id, meds in manager.medications.items():
        print(f"  Patient {patient_id}:")
        for med in meds:
            print(f"    - {med.name} ({med.dosage}) at {med.reminder_times}")
    
    print(f"\n📊 Pending reminders: {len(manager.pending_reminders)}")


if __name__ == "__main__":
    asyncio.run(main())
