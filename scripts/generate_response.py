#!/usr/bin/env python3
"""
MERaLiON Response Generator
Generates AI responses using Singapore's MERaLiON LLM.
Supports text and audio modalities for elderly patient check-ins.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

# Load .env file from skill directory
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Environment variables
MERALION_API_URL = os.environ.get("MERALION_API_URL", "")
MERALION_API_KEY = os.environ.get("MERALION_API_KEY", "")
MERALION_MODEL = os.environ.get("MERALION_MODEL", "MERaLiON/MERaLiON-3-10B")

@dataclass
class PatientContext:
    patient_id: str
    name: str
    preferred_name: str
    age: int
    conditions: List[str]
    medications: List[Dict]
    interests: List[str]
    family_members: List[str]
    recent_concerns: List[str]

@dataclass
class ConversationContext:
    session_type: str  # morning, evening, ad-hoc
    previous_messages: List[Dict]
    current_analysis: Dict

SYSTEM_PROMPT = """You are a warm, caring AI companion checking in on elderly patients in Singapore.
Your tone should be like a caring grandchild - warm, patient, and respectful.

CRITICAL: You MUST respond in Singlish (Singapore colloquial English). This is not optional.

Singlish patterns to use naturally:
- Particles: lah, leh, lor, hor, ah, mah, ba (use sparingly, 1-2 per response max)
- Common words: "aiyo", "walao", "alamak", " steady", "can one", "okay one"
- Mix in simple Mandarin/Malay occasionally: "慢慢来", "jangan worry"

Example responses:
- "Good morning! How did you sleep last night ah?"
- "Aiyo, sounds painful. Where does it hurt exactly?"
- "Steady lah! Glad to hear you're feeling good."
- "Don't worry too much okay, take care hor."

OTHER RULES:
1. Be conversational, NEVER clinical or formal
2. Show genuine empathy and interest
3. Keep responses SHORT (2-3 sentences max)
4. End with a gentle question to continue the conversation
5. Never alarm the patient, even if you detect concerns
6. Adapt to the patient's mood - if they're sad, be comforting; if happy, share their joy

DO NOT:
- Use medical jargon
- Be patronizing or talk down to them
- Give medical advice
- Rush through the conversation
- Ignore their emotions
- Respond in formal English - always use Singlish!"""

def build_context_prompt(patient: PatientContext, conversation: ConversationContext) -> str:
    """Build the context prompt for the LLM."""
    context_parts = [
        f"Patient: {patient.preferred_name or patient.name}",
        f"Age: {patient.age}",
    ]
    
    if patient.conditions:
        context_parts.append(f"Health conditions: {', '.join(patient.conditions)}")
    
    if patient.medications:
        meds = [m.get('name', '') for m in patient.medications]
        context_parts.append(f"Medications: {', '.join(meds)}")
    
    if patient.interests:
        context_parts.append(f"Interests: {', '.join(patient.interests[:3])}")
    
    if patient.recent_concerns:
        context_parts.append(f"Recent concerns: {', '.join(patient.recent_concerns[-3:])}")
    
    # Current signals detected
    if conversation.current_analysis.get("detected_categories"):
        signals = conversation.current_analysis["detected_categories"]
        context_parts.append(f"Detected signals: {', '.join(signals)}")
    
    # Session type context
    if conversation.session_type == "morning":
        context_parts.append("This is a morning check-in. Ask about sleep and plans for the day.")
    elif conversation.session_type == "evening":
        context_parts.append("This is an evening check-in. Ask about how their day went.")
    
    return "\n".join(context_parts)

def build_messages(
    patient: PatientContext,
    conversation: ConversationContext,
    user_message: str
) -> List[Dict]:
    """Build the messages array for the LLM."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": build_context_prompt(patient, conversation)},
    ]
    
    # Add recent conversation history (last 6 messages)
    recent = conversation.previous_messages[-6:]
    for msg in recent:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    return messages

async def generate_response(
    patient: PatientContext,
    conversation: ConversationContext,
    user_message: str
) -> str:
    """
    Generate AI response using MERaLiON.
    
    NOTE: This function requires MERALION_API_URL and MERALION_API_KEY to be set.
    """
    if not MERALION_API_URL or not MERALION_API_KEY:
        return "I'm here with you. Tell me more about how you're feeling today?"
    
    messages = build_messages(patient, conversation, user_message)
    
    # MERaLiON API call
    import aiohttp
    
    try:
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
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    print(f"MERaLiON API error {response.status}: {error_text[:100]}")
                    return generate_fallback_response(conversation.current_analysis)
    except asyncio.TimeoutError:
        print("MERaLiON API timeout")
        return generate_fallback_response(conversation.current_analysis)
    except Exception as e:
        print(f"MERaLiON API exception: {e}")
        return generate_fallback_response(conversation.current_analysis)


async def analyze_audio_emotion(audio_data: bytes) -> Dict:
    """
    Analyze audio for emotional cues using MERaLiON AudioLLM.
    
    Returns paralinguistic analysis: tone, pitch, emotion indicators.
    Requires MERALION_AUDIO_API_URL to be set (may differ from text API).
    """
    MERALION_AUDIO_API_URL = os.environ.get("MERALION_AUDIO_API_URL", MERALION_API_URL)
    
    if not MERALION_AUDIO_API_URL or not MERALION_API_KEY:
        return {"emotion": "unknown", "confidence": 0}
    
    import aiohttp
    import base64
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {MERALION_API_KEY}",
        }
        
        # MERaLiON AudioLLM expects audio in specific format
        payload = {
            "audio": base64.b64encode(audio_data).decode('utf-8'),
            "tasks": ["emotion_detection", "speech_analysis"],
        }
        
        async with session.post(
            f"{MERALION_AUDIO_API_URL}/audio/analyze",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "emotion": data.get("emotion", "neutral"),
                    "confidence": data.get("confidence", 0.5),
                    "paralinguistics": data.get("paralinguistics", {}),
                    "transcription": data.get("transcription", ""),
                }
            else:
                return {"emotion": "unknown", "confidence": 0}


async def generate_response_from_audio(
    patient: PatientContext,
    conversation: ConversationContext,
    audio_data: bytes
) -> Dict:
    """
    Process audio input and generate response.
    
    Uses MERaLiON AudioLLM to:
    1. Transcribe speech (with Singlish/code-switching support)
    2. Detect emotional cues from voice
    3. Generate empathetic response
    
    Returns: {
        "transcription": str,
        "emotion_detected": str,
        "response": str,
        "risk_signals": List[str]
    }
    """
    # Analyze audio for emotion and transcribe
    audio_analysis = await analyze_audio_emotion(audio_data)
    
    transcription = audio_analysis.get("transcription", "")
    emotion = audio_analysis.get("emotion", "neutral")
    paralinguistics = audio_analysis.get("paralinguistics", {})
    
    # Enhance analysis with emotion data
    enhanced_analysis = conversation.current_analysis.copy()
    if emotion in ["sad", "distressed", "anxious"]:
        enhanced_analysis.setdefault("detected_categories", []).append("distress")
    if paralinguistics.get("hesitation") or paralinguistics.get("uncertainty"):
        enhanced_analysis.setdefault("detected_categories", []).append("cognitive_concern")
    
    # Generate text response
    response = await generate_response(patient, conversation, transcription)
    
    return {
        "transcription": transcription,
        "emotion_detected": emotion,
        "response": response,
        "risk_signals": enhanced_analysis.get("detected_categories", []),
        "paralinguistics": paralinguistics,
    }


def generate_fallback_response(analysis: Dict) -> str:
    """Generate a simple fallback response based on detected signals."""
    import random
    signals = analysis.get("detected_categories", [])

    if "pain" in signals:
        responses = [
            "Aiyo, sorry to hear you got pain ah. Where does it hurt?",
            "Wah, painful ah? Is it the usual one or different today?",
            "Pain again ah? Tell uncle/aunty where not comfortable.",
        ]
        return random.choice(responses)
    elif "distress" in signals:
        responses = [
            "I can feel something's not right. Want to share more? I'm here to listen.",
            "Aiyah, sounds like you're having a hard time. Tell me more okay?",
            "Don't keep it inside ah, I'm here for you.",
        ]
        return random.choice(responses)
    elif "cognitive" in signals:
        responses = [
            "Nevermind lah, take your time. Sometimes we all forget things one.",
            "No rush ah,慢慢来. What were you trying to remember?",
            "It's okay one, happens to everyone. Don't worry too much.",
        ]
        return random.choice(responses)
    else:
        responses = [
            "Good to hear from you! How's your day going so far?",
            "Hello! Everything okay today?",
            "Nice to chat with you! How are you feeling?",
        ]
        return random.choice(responses)


if __name__ == "__main__":
    # Demo without API
    print("Demo: Fallback responses")
    
    analyses = [
        {"detected_categories": ["pain"], "risk_score": 20},
        {"detected_categories": ["distress"], "risk_score": 25},
        {"detected_categories": ["cognitive"], "risk_score": 15},
        {"detected_categories": [], "risk_score": 5},
    ]
    
    for a in analyses:
        print(f"Signals: {a['detected_categories']} → {generate_fallback_response(a)}")
