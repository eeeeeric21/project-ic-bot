#!/usr/bin/env python3
"""
Project IC Check-in Bot
Main bot for conducting elderly patient check-ins.

Usage:
    python checkin_bot.py --mode telegram    # Run as Telegram bot
    python checkin_bot.py --mode cli          # Run in interactive CLI mode
    python checkin_bot.py --patient <id>      # Check-in specific patient
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Supabase
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except ImportError:
    supabase = None
    print("⚠️ Supabase not installed. Database features disabled.")

# Import our modules
from generate_response import (
    PatientContext,
    ConversationContext,
    generate_response,
    generate_fallback_response
)
from analyze import analyze_response


class CheckinBot:
    """Main check-in bot class."""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}  # patient_id -> session data
        
    def get_patient(self, patient_id: str) -> Optional[PatientContext]:
        """Load patient from database."""
        if not supabase:
            return self._get_demo_patient(patient_id)
        
        try:
            result = supabase.table("patients").select("*").eq("id", patient_id).execute()
            if result.data:
                p = result.data[0]
                return PatientContext(
                    patient_id=p["id"],
                    name=p["name"],
                    preferred_name=p.get("preferred_name") or p["name"],
                    age=p.get("age", 0),
                    conditions=p.get("conditions", []),
                    medications=p.get("medications", []),
                    interests=p.get("interests", []),
                    family_members=p.get("family_members", []),
                    recent_concerns=[]
                )
        except Exception as e:
            print(f"Error loading patient: {e}")
        
        return None
    
    def _get_demo_patient(self, patient_id: str) -> PatientContext:
        """Return demo patient for testing."""
        return PatientContext(
            patient_id=patient_id,
            name="Tan Ah Kow",
            preferred_name="Uncle Tan",
            age=72,
            conditions=["diabetes", "hypertension", "knee arthritis"],
            medications=[{"name": "Metformin", "dosage": "500mg", "frequency": "twice daily"}],
            interests=["gardening", "mahjong", "grandchildren"],
            family_members=[{"name": "Sarah", "relationship": "daughter"}],
            recent_concerns=["knee pain"]
        )
    
    def list_patients(self) -> List[Dict]:
        """List all active patients."""
        if not supabase:
            return [{"id": "demo-001", "name": "Uncle Tan", "age": 72}]
        
        try:
            result = supabase.table("patients").select("id, name, preferred_name, age").eq("is_active", True).execute()
            return result.data
        except Exception as e:
            print(f"Error listing patients: {e}")
            return []
    
    async def start_checkin(self, patient_id: str) -> Dict:
        """Start a new check-in session."""
        patient = self.get_patient(patient_id)
        if not patient:
            return {"error": "Patient not found"}
        
        # Determine session type based on time
        hour = datetime.now().hour
        if 6 <= hour < 12:
            session_type = "morning"
        elif 17 <= hour < 21:
            session_type = "evening"
        else:
            session_type = "ad-hoc"
        
        # Create session
        session = {
            "patient": patient,
            "session_type": session_type,
            "messages": [],
            "signals": [],
            "risk_score": 0,
            "started_at": datetime.now().isoformat()
        }
        
        self.active_sessions[patient_id] = session
        
        # Generate opening message
        greeting = "Good morning" if session_type == "morning" else "Good evening" if session_type == "evening" else "Hello"
        
        opening = f"{greeting}, {patient.preferred_name}! How are you feeling today?"
        
        session["messages"].append({"role": "assistant", "content": opening})
        
        return {
            "status": "started",
            "patient_id": patient_id,
            "patient_name": patient.preferred_name,
            "session_type": session_type,
            "opening_message": opening
        }
    
    async def process_message(self, patient_id: str, user_message: str) -> Dict:
        """Process a patient message and return AI response."""
        session = self.active_sessions.get(patient_id)
        if not session:
            # Auto-start session
            await self.start_checkin(patient_id)
            session = self.active_sessions.get(patient_id)
        
        patient = session["patient"]
        
        # Analyze message
        analysis = analyze_response(user_message)
        
        # Get risk from analysis
        msg_risk = analysis.risk_score
        session["risk_score"] += msg_risk
        
        # Track signals
        if analysis.detected_categories:
            session["signals"].extend(analysis.detected_categories)
        
        # Build conversation context
        conversation = ConversationContext(
            session_type=session["session_type"],
            previous_messages=session["messages"],
            current_analysis={
                "detected_categories": analysis.detected_categories,
                "risk_score": analysis.risk_score,
                "signals": analysis.signals
            }
        )
        
        # Get AI response
        try:
            ai_response = await generate_response(patient, conversation, user_message)
        except Exception as e:
            print(f"MERaLiON error: {e}")
            ai_response = generate_fallback_response(analysis)
        
        # Store messages
        session["messages"].append({
            "role": "user", 
            "content": user_message, 
            "analysis": {
                "detected_categories": analysis.detected_categories,
                "risk_score": analysis.risk_score
            }
        })
        session["messages"].append({"role": "assistant", "content": ai_response})
        
        # Determine if alert needed
        alert_needed = session["risk_score"] >= 30 or msg_risk >= 50
        
        return {
            "response": ai_response,
            "detected_signals": analysis.detected_categories,
            "message_risk": msg_risk,
            "total_risk": session["risk_score"],
            "alert_needed": alert_needed,
            "keywords": analysis.red_flags
        }
    
    async def end_checkin(self, patient_id: str) -> Dict:
        """End check-in session and save to database."""
        session = self.active_sessions.get(patient_id)
        if not session:
            return {"error": "No active session"}
        
        # Determine risk level
        score = session["risk_score"]
        if score >= 50:
            risk_level = "RED"
        elif score >= 30:
            risk_level = "ORANGE"
        elif score >= 15:
            risk_level = "YELLOW"
        else:
            risk_level = "GREEN"
        
        # Save to database
        checkin_record = {
            "patient_id": patient_id,
            "session_type": session["session_type"],
            "started_at": session["started_at"],
            "ended_at": datetime.now().isoformat(),
            "detected_categories": list(set(session["signals"])),
            "risk_score": score,
            "risk_level": risk_level,
            "summary": f"Check-in completed with {len(session['messages'])} messages"
        }
        
        if supabase:
            try:
                # Save check-in
                result = supabase.table("checkins").insert(checkin_record).execute()
                checkin_id = result.data[0]["id"]
                
                # Save messages
                for msg in session["messages"]:
                    supabase.table("messages").insert({
                        "checkin_id": checkin_id,
                        "patient_id": patient_id,
                        "role": msg["role"],
                        "content": msg["content"]
                    }).execute()
                
                # Create alert if needed
                if risk_level in ["ORANGE", "RED"]:
                    await self._create_alert(patient_id, checkin_id, risk_level, score, session["signals"])
                    
            except Exception as e:
                print(f"Database error: {e}")
        
        # Clear session
        del self.active_sessions[patient_id]
        
        return {
            "status": "completed",
            "risk_level": risk_level,
            "risk_score": score,
            "signals": list(set(session["signals"])),
            "message_count": len(session["messages"])
        }
    
    async def _create_alert(self, patient_id: str, checkin_id: str, level: str, score: int, signals: list):
        """Create and send alert."""
        patient = self.get_patient(patient_id)
        if not patient:
            return
        
        # Save to database
        if supabase:
            alert_data = {
                "patient_id": patient_id,
                "checkin_id": checkin_id,
                "alert_level": level,
                "title": f"{level} Alert - {patient.preferred_name}",
                "detected_issues": list(set(signals)),
                "message": f"Risk score: {score}"
            }
            supabase.table("alerts").insert(alert_data).execute()
        
        # Send Telegram notification
        await self._send_telegram_alert(patient, level, score, signals)
    
    async def _send_telegram_alert(self, patient: PatientContext, level: str, score: int, signals: list):
        """Send alert via Telegram."""
        import aiohttp
        
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CASE_WORKER_CHAT_ID")
        
        if not bot_token or not chat_id:
            print("⚠️ Telegram not configured")
            return
        
        emoji = {"RED": "🚨", "ORANGE": "⚠️", "YELLOW": "📋"}.get(level, "ℹ️")
        
        message = f"""{emoji} *Project IC Alert*

*Patient:* {patient.preferred_name} (Age {patient.age})
*Level:* {level}
*Score:* {score}

*Issues:*
{chr(10).join(f'• {s}' for s in set(signals))}

_Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}_
"""
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            async with session.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }) as resp:
                if resp.status == 200:
                    print(f"✅ Telegram alert sent ({level})")
                else:
                    print(f"❌ Failed to send alert")


# CLI Mode
async def cli_mode():
    """Run check-in in interactive CLI mode."""
    bot = CheckinBot()
    
    print("\n" + "=" * 60)
    print("🏥 PROJECT IC - Check-in Bot (CLI Mode)")
    print("=" * 60)
    
    # List patients
    patients = bot.list_patients()
    print("\n📋 Available Patients:")
    for i, p in enumerate(patients, 1):
        print(f"  {i}. {p.get('preferred_name') or p['name']} (Age {p.get('age', '?')})")
    
    # Select patient
    if not patients:
        print("No patients found. Using demo patient.")
        patient_id = "demo-001"
    else:
        choice = input("\nSelect patient (number) or press Enter for demo: ").strip()
        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(patients):
                patient_id = patients[idx]["id"]
            else:
                patient_id = "demo-001"
        else:
            patient_id = "demo-001"
    
    # Start check-in
    result = await bot.start_checkin(patient_id)
    print(f"\n🤖 {result['opening_message']}")
    
    # Conversation loop
    while True:
        user_input = input(f"\n👤 You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ["/end", "/quit", "/bye", "exit"]:
            break
        
        # Process message
        response = await bot.process_message(patient_id, user_input)
        
        print(f"\n🤖 AI: {response['response']}")
        
        if response['detected_signals']:
            print(f"   📊 Signals: {response['detected_signals']} | Risk: {response['total_risk']}")
        
        if response['alert_needed']:
            print("   ⚠️ ALERT TRIGGERED!")
    
    # End session
    final = await bot.end_checkin(patient_id)
    print(f"\n{'=' * 60}")
    print(f"📋 Session Complete")
    print(f"   Risk Level: {final['risk_level']}")
    print(f"   Risk Score: {final['risk_score']}")
    print(f"{'=' * 60}\n")


# Main
async def main():
    parser = argparse.ArgumentParser(description="Project IC Check-in Bot")
    parser.add_argument("--mode", choices=["cli", "telegram"], default="cli", help="Run mode")
    parser.add_argument("--patient", help="Patient ID for check-in")
    
    args = parser.parse_args()
    
    if args.mode == "cli":
        await cli_mode()
    elif args.mode == "telegram":
        print("Telegram bot mode coming soon!")
        print("For now, use --mode cli")


if __name__ == "__main__":
    asyncio.run(main())
