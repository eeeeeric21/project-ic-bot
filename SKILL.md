---
name: project-ic-checkin
description: Conversational AI engine for daily health check-ins with elderly patients. Handles natural conversation flow, signal detection, and risk scoring. Use when building or testing the core check-in conversation functionality.
---

# Project IC: Check-in Conversation Engine

Core conversation logic for elderly patient check-ins.

**Powered by MERaLiON** - Singapore's multimodal LLM with:
- Singlish & code-switching support
- Audio/speech processing
- Paralinguistic emotion detection

## Quick Start

```bash
# Run interactive demo (3 scenarios)
python scripts/demo_checkin.py

# Interactive CLI check-in
python scripts/checkin_bot.py --mode cli

# Start Telegram bot (text + voice)
python scripts/telegram_voice_bot.py

# Test signal detection
python scripts/analyze.py "I'm feeling sad and my knees hurt today"
```

## Bot Features

### Telegram Bot (@AesculAI_helper_bot)
- **Proactive Check-ins** - Bot initiates daily conversations 📅
  - Morning: 8:00 AM 🌅
  - Afternoon: 2:00 PM 🌤️
- **Wake Words** - Say "Hello Aescul Helper" to start 🗣️
- **Voice Input** - Patient speaks, bot listens (ASR) 🎤
- **Voice Output** - Bot speaks back naturally (TTS) 🔊
- **Text check-ins** - Message the bot directly
- **Real-time alerts** - Case workers get notified instantly
- **Singlish support** - Natural local language responses

### Voice Flow
```
Proactive Check-in (8AM/2PM) 📅
         OR
Patient says "Hello Aescul Helper" 🗣️
         ↓
[ASR] Transcribe to text (if voice)
         ↓
[AI] MERaLiON responds in Singlish
         ↓
[TTS] Convert to speech
         ↓
Bot speaks back 🗣️
```

### Commands
| Command | Description |
|---------|-------------|
| `/start` | Register and begin check-in |
| `/end` | Complete check-in and get summary |
| `/status` | View current session status |

### Wake Words
Say any of these to start a check-in:
- "Hello Aescul Helper"
- "Hello AesculAI"
- "Hi Aescul"
- "Start check-in"

### Voice Configuration
Set in `.env`:
```env
VOICE_OUTPUT=true  # Enable voice responses
TTS_PROVIDER=edge  # Options: edge, openai, elevenlabs
```

## Demo Output Example

```
============================================================
🏥 PROJECT IC - Check-in Demo (PAIN)
============================================================
Patient: Uncle Tan (Age 72)
Conditions: diabetes, hypertension, knee arthritis
============================================================

👤 Uncle Tan: My knee is very painful today.
🤖 AI: Wah lau, sorry to hear that ah. Is it the usual pain or worse?
   📊 Signals: ['pain'] | Risk: +8

============================================================
📋 CHECK-IN SUMMARY
============================================================
Total Risk Score: 11
Risk Level: 🟢 GREEN
Action: Continue monitoring
```

## Components

| File | Purpose |
|------|---------|
| `references/prompts.md` | Conversation prompts library |
| `references/keywords.md` | Detection keyword lists |
| `references/responses.md` | Template responses for signals |
| `scripts/analyze.py` | Signal detection logic |
| `scripts/risk_score.py` | Risk calculation |
| `scripts/generate_response.py` | MERaLiON API integration |

## Signal Categories

| Category | Weight | Examples |
|----------|--------|----------|
| Pain | 5 | "hurt", "pain", "ache", "sore" |
| Cognitive | 3 | "forget", "confused", "lost" |
| Distress | 4 | "sad", "lonely", "scared" |
| Red Flags | 50+ | "can't breathe", "chest pain", "fall" |

## Risk Levels

- **GREEN (0-15)**: Normal, continue monitoring
- **YELLOW (15-30)**: Flag for review
- **ORANGE (30-50)**: Notify case worker
- **RED (50+)**: Immediate escalation

## Environment Variables

```env
# MERaLiON TextLLM (for text-based check-ins)
MERALION_API_URL=http://meralion.org:8010/v1
MERALION_API_KEY=your_api_key
MERALION_MODEL=MERaLiON/MERaLiON-3-10B

# MERaLiON AudioLLM (optional, for voice-based check-ins)
# Falls back to MERALION_API_URL if not set
MERALION_AUDIO_API_URL=<optional, same as above if unified>

# Database
SUPABASE_URL=<get from supabase>
SUPABASE_ANON_KEY=<get from supabase>
```

## Available MERaLiON Models

| Model | Use Case |
|-------|----------|
| `MERaLiON/MERaLiON-3-10B` | Text conversations (default) ✅ |
| `MERaLiON/MERaLiON-2-10B` | Older text model |
| `MERaLiON/MERaLiON-2-10B-ASR` | Audio/speech recognition 🔧 |
| `MERaLiON/MERaLiON-ASR-EXP` | Experimental ASR 🔧 |
| `TRANSLATION/MALAY` | Malay translation |
| `TRANSLATION/TAMIL` | Tamil translation |

✅ = Working | 🔧 = Requires specific endpoint configuration

## Audio Capabilities (MERaLiON AudioLLM)

When patients speak instead of type, MERaLiON can:
- **Transcribe** Singlish and code-switched speech
- **Detect emotions** from voice tone, pitch, hesitation
- **Identify distress** that text might hide

Audio analysis returns:
```json
{
  "transcription": "I'm okay lah, just a bit tired",
  "emotion_detected": "sad",
  "paralinguistics": {
    "hesitation": true,
    "pitch_variation": "low"
  },
  "risk_signals": ["distress"]
}
```
