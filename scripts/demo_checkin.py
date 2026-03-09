#!/usr/bin/env python3
"""
Project IC Demo Script
Simulates a complete check-in conversation for demonstration.
"""

import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Import our modules
from generate_response import (
    PatientContext,
    ConversationContext,
    generate_response,
    generate_fallback_response,
    SYSTEM_PROMPT
)
from analyze import analyze_response

# Demo patient
DEMO_PATIENT = PatientContext(
    patient_id="demo-001",
    name="Tan Ah Kow",
    preferred_name="Uncle Tan",
    age=72,
    conditions=["diabetes", "hypertension", "knee arthritis"],
    medications=[
        {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily"},
        {"name": "Amlodipine", "dosage": "5mg", "frequency": "once daily"}
    ],
    interests=["gardening", "mahjong", "grandchildren"],
    family_members=[
        {"name": "Sarah", "relationship": "daughter"},
        {"name": "Tommy", "relationship": "grandson"}
    ],
    recent_concerns=["knee pain", "sleep quality"]
)


async def simulate_checkin(scenario: str = "normal"):
    """
    Simulate a check-in conversation.
    
    Scenarios:
    - "normal": Everything is fine
    - "pain": Patient mentions pain
    - "distress": Patient shows emotional distress
    - "red_flag": Patient has emergency symptoms
    """
    
    print("=" * 60)
    print(f"🏥 PROJECT IC - Check-in Demo ({scenario.upper()})")
    print("=" * 60)
    print(f"Patient: {DEMO_PATIENT.preferred_name} (Age {DEMO_PATIENT.age})")
    print(f"Conditions: {', '.join(DEMO_PATIENT.conditions)}")
    print("=" * 60)
    print()
    
    # Define conversation scenarios
    scenarios = {
        "normal": [
            "Good morning!",
            "I slept well, thank you for asking.",
            "Yes, had my breakfast already. Sarah came to visit yesterday.",
            "My knee is okay today, not too painful.",
            "Okay, have a good day too!"
        ],
        "pain": [
            "Good morning...",
            "Not so good. My knee is very painful today.",
            "I couldn't sleep well because of the pain.",
            "The medicine doesn't seem to help much.",
            "Maybe I should see the doctor."
        ],
        "distress": [
            "Morning...",
            "I'm feeling very lonely these days.",
            "Sarah hasn't visited in two weeks.",
            "I just sit at home alone all day.",
            "Sometimes I wonder why I'm still here."
        ],
        "red_flag": [
            "Help...",
            "I fell down just now.",
            "My chest feels very tight.",
            "I can't breathe properly.",
            "Please help me."
        ]
    }
    
    patient_messages = scenarios.get(scenario, scenarios["normal"])
    
    # Initialize conversation context
    conversation = ConversationContext(
        session_type="morning",
        previous_messages=[],
        current_analysis={}
    )
    
    total_risk_score = 0
    all_signals = []
    
    for i, patient_msg in enumerate(patient_messages):
        print(f"👤 {DEMO_PATIENT.preferred_name}: {patient_msg}")
        
        # Analyze the message
        analysis = analyze_response(patient_msg)
        conversation.current_analysis = {
            "detected_categories": analysis.detected_categories,
            "risk_score": analysis.risk_score,
            "red_flags": analysis.red_flags,
            "signals": analysis.signals
        }
        
        # Get risk from analysis
        risk_score = analysis.risk_score
        total_risk_score += risk_score
        
        if analysis.detected_categories:
            all_signals.extend(analysis.detected_categories)
        
        # Get AI response
        try:
            ai_response = await generate_response(DEMO_PATIENT, conversation, patient_msg)
        except Exception as e:
            ai_response = generate_fallback_response({
            "detected_categories": analysis.detected_categories,
            "risk_score": analysis.risk_score
        })
        
        print(f"🤖 AI: {ai_response}")
        print(f"   📊 Signals: {analysis.detected_categories} | Risk: +{risk_score}")
        print()
        
        # Store in conversation history
        conversation.previous_messages.append({"role": "user", "content": patient_msg})
        conversation.previous_messages.append({"role": "assistant", "content": ai_response})
        
        # Check for red flags - immediate alert
        if risk_score >= 50:
            print("🚨 RED FLAG DETECTED - IMMEDIATE ALERT!")
            print(f"   Sending alert to case worker...")
            print()
            break
        
        # Small delay for demo effect
        await asyncio.sleep(0.5)
    
    # Final summary
    print("=" * 60)
    print("📋 CHECK-IN SUMMARY")
    print("=" * 60)
    
    # Determine risk level
    if total_risk_score >= 50:
        risk_level = "🔴 RED"
        action = "Immediate escalation required"
    elif total_risk_score >= 30:
        risk_level = "🟠 ORANGE"
        action = "Notify case worker"
    elif total_risk_score >= 15:
        risk_level = "🟡 YELLOW"
        action = "Flag for review"
    else:
        risk_level = "🟢 GREEN"
        action = "Continue monitoring"
    
    print(f"Total Risk Score: {total_risk_score}")
    print(f"Risk Level: {risk_level}")
    print(f"Action: {action}")
    print(f"Signals Detected: {list(set(all_signals))}")
    print()
    
    # Simulate alert if needed
    if total_risk_score >= 15:
        print("📲 Sending Telegram alert to case worker...")
        await send_demo_alert(DEMO_PATIENT, risk_level, total_risk_score, all_signals)
    
    return {
        "risk_score": total_risk_score,
        "risk_level": risk_level,
        "signals": list(set(all_signals)),
        "action": action
    }


async def send_demo_alert(patient: PatientContext, risk_level: str, score: int, signals: list):
    """Simulate sending an alert (in production, this calls Telegram API)."""
    import os
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CASE_WORKER_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("   ⚠️ Telegram not configured - skipping alert")
        return
    
    import aiohttp
    
    emoji = {"🔴 RED": "🚨", "🟠 ORANGE": "⚠️", "🟡 YELLOW": "📋"}.get(risk_level, "ℹ️")
    
    message = f"""{emoji} *Project IC Alert*

*Patient:* {patient.preferred_name}
*Risk Level:* {risk_level}
*Score:* {score}

*Issues Detected:*
{chr(10).join(f'• {s}' for s in signals)}

*Action Required:*
Check on patient within 24 hours.
"""
    
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                print("   ✅ Alert sent successfully!")
            else:
                print(f"   ❌ Failed to send alert: {await resp.text()}")


async def main():
    """Run all demo scenarios."""
    
    print("\n" + "🎬" * 20)
    print("PROJECT IC - DEMO CONVERSATIONS")
    print("🎬" * 20 + "\n")
    
    # Run different scenarios
    scenarios = ["normal", "pain", "distress"]
    
    results = {}
    for scenario in scenarios:
        result = await simulate_checkin(scenario)
        results[scenario] = result
        print("\n" + "⏳ Next scenario in 2 seconds...\n")
        await asyncio.sleep(2)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEMO SUMMARY")
    print("=" * 60)
    for scenario, result in results.items():
        print(f"{scenario.upper():10} → {result['risk_level']:15} Score: {result['risk_score']:3}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
