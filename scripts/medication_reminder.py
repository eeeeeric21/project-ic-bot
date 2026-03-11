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
    
    async def send_reminder(self, patient_id: str, medication: Medication, time_str: str):
        """Send a medication reminder to a patient."""
        if not self.bot_token:
            logger.error("BOT_TOKEN not set")
            return False
        
        # Build message
        med_info = f"{medication.name}"
        if medication.dosage:
            med_info += f" ({medication.dosage})"
        
        instructions = f"\n📝 {medication.instructions}" if medication.instructions else ""
        
        message = f"""💊 *Medication Reminder*

Time to take your medicine:
• {med_info}{instructions}

Reply:
• "taken" - when you've taken it
• "skip" - if you need to skip

_Stay healthy! 💙_"""
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": patient_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        # Track this reminder
                        reminder_id = f"{patient_id}-{medication.id}-{datetime.now(SG_TIMEZONE).strftime('%Y%m%d')}-{time_str.replace(':', '')}"
                        self.pending_reminders[reminder_id] = MedicationReminder(
                            id=reminder_id,
                            medication_id=medication.id,
                            patient_id=patient_id,
                            scheduled_time=datetime.now(SG_TIMEZONE)
                        )
                        
                        logger.info(f"✅ Sent medication reminder to {patient_id}: {medication.name}")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"Failed to send reminder: {error}")
                        return False
            except Exception as e:
                logger.error(f"Error sending reminder: {e}")
                return False
    
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
        
        for reminder in self.pending_reminders.values():
            if reminder.patient_id == patient_id:
                if reminder.status == "taken":
                    taken += 1
                elif reminder.status == "skipped":
                    skipped += 1
                elif reminder.status == "missed":
                    missed += 1
        
        total = taken + skipped + missed
        adherence_rate = (taken / total * 100) if total > 0 else 0
        
        return {
            "patient_id": patient_id,
            "period_days": days,
            "total_doses": total,
            "taken": taken,
            "skipped": skipped,
            "missed": missed,
            "adherence_rate": round(adherence_rate, 1)
        }


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
