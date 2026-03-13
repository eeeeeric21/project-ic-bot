# Project AesculAI - AI Health Companion for Elderly Care

<div align="center">

# Project AesculAI

**🤖 AI-Powered Daily Health Check-ins for Elderly Patients Living Alone**

[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue)](https://t.me/AesculAI_helper_bot)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Telegram%20%7C%20PWA%20%7C%20Alexa-lightgrey)]()

**Implementation Status:** [Telegram ✅ 100%] [PWA ⚠️ 30%] [Alexa 🚧 40%]

</div>

---

## 🎯 Implementation Status (March 2026)

### ✅ Fully Working (Production Ready)
- **Telegram Bot** - Primary interface, 100% functional
  - All 15+ commands working
  - MERaLiON AI conversations
  - Medication reminders
  - Health alerts
  - **Try it now:** [@AesculAI_helper_bot](https://t.me/AesculAI_helper_bot)

### ⚠️ Partially Implemented
- **Web PWA** - UI complete, not yet deployed
  - Landing page, chat interface, dashboard designed
  - Currently uses mock data
  - Not connected to backend yet
  - **Status:** Planned for Phase 2

### 🚧 Designed but Not Deployed
- **Alexa Skill** - Code ready, not deployed
  - Handler code written
  - Intent model designed
  - Needs Cloud Functions deployment
  - **Status:** Planned for Phase 3

**For detailed status, see:** [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Telegram Bot Guide](#telegram-bot-guide)
- [Web Dashboard (PWA)](#web-dashboard-pwa)
- [Alexa Skill](#alexa-skill)
- [Command Reference](#command-reference)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

**Project AesculAI** is an AI-powered daily health check-in system designed for elderly patients living alone. Using natural conversations in Singlish, the system monitors physical and mental health, detects concerning signals, and alerts caregivers when needed.

### Key Highlights

- 🇸🇬 **Singapore-Focused** - Understands Singlish and local context
- 💬 **Natural Conversations** - No robotic interactions, just friendly chats
- 🔔 **Smart Alerts** - Automatic escalation to caregivers
- 📊 **Health Monitoring** - Tracks physical, mental, and cognitive health
- 💊 **Medication Reminders** - Never miss a dose
- 📈 **Weekly Reports** - Comprehensive health summaries

---

## ✨ Features

### For Patients 👴👵 (Telegram Bot - ✅ Fully Working)

- ✅ **Daily Check-ins** - 8 AM morning, 2 PM afternoon
- ✅ **Voice Conversations** - Speak naturally in Singlish
- ✅ **Health Tracking** - Pain, mood, sleep, appetite monitoring
- ✅ **Medication Reminders** - With skip/taken buttons
- ✅ **Emergency Detection** - Chest pain, falls, breathing issues

### For Caregivers 👨‍⚕️👩‍⚕️ (Telegram Bot - ✅ Fully Working)

- ✅ **Health Alerts** - Risk-level based notifications (YELLOW/ORANGE/RED)
- ✅ **Medication Management** - Add, edit, view medications
- ✅ **Adherence Reports** - Track medication compliance
- ✅ **Weekly Summaries** - Comprehensive health reports
- ✅ **Multi-Patient Monitoring** - Monitor multiple patients

### Web Dashboard (PWA - ⚠️ UI Only, Not Deployed)

**Currently Built:**
- Landing page with feature overview
- Chat interface (demo mode)
- Dashboard with mock data

**Needs:**
- Vercel deployment
- Backend integration
- Authentication

### Alexa Skill (🚧 Designed, Not Deployed)

**Currently Ready:**
- Intent model designed
- Handler code written
- Conversation flow planned

**Needs:**
- Alexa Developer Console setup
- Cloud Functions deployment
- Account linking configuration

---

## 🚀 Quick Start

### Step 1: Start the Bot

Search for **@AesculAI_helper_bot** in Telegram and click "Start"

### Step 2: Register Your Role

Choose your role:
- **Patient**: `/registerpatient`
- **Caregiver**: `/registercaseworker`
- **Both**: Run both commands!

### Step 3: Start Using

**As a Patient:**
- Say "Hello Aescul Helper"
- Or just send any message
- Have a natural conversation about your health

**As a Caregiver:**
- `/assign <patient_name>` - Assign patients to yourself
- `/addmed <patient> <med> <dosage> <time>` - Add medications
- `/listmed <patient>` - View medications

---

## 📱 Telegram Bot Guide

### Getting Started

#### 1. Register as a Patient

```
/registerpatient
```

You'll receive:
- ✅ Daily check-ins at 8 AM and 2 PM
- ✅ Medication reminders (if set up)
- ✅ Health monitoring through conversations

**Test it:**
- Say: "Hello Aescul Helper"
- Type: "I'm feeling tired today"
- The bot responds with empathetic conversation

#### 2. Register as a Caregiver

```
/registercaseworker
```

You'll be able to:
- ✅ Assign patients to yourself
- ✅ Manage medications
- ✅ Receive health alerts
- ✅ Generate reports

#### 3. Assign Patients

```
/assign <patient_name>
```

Example: `/assign John`

This links the patient to you for monitoring.

### Daily Check-ins

#### Starting a Check-in

**Option 1: Proactive (Automatic)**
- Bot sends check-in at 8 AM and 2 PM
- Just reply naturally

**Option 2: On-Demand**
- Say "Hello Aescul Helper"
- Or send any message

#### During Check-in

**Conversation Examples:**

```
You: "I'm feeling a bit tired today"
Bot: "Aiyo, tired ah? Did you sleep well last night, hor?"
```

```
You: "My knee is painful"
Bot: "Wah lau, sorry to hear that. Is it the usual pain or worse than normal?"
```

```
You: "I didn't sleep well, kept waking up"
Bot: "Aiyah, sleep problem again. Have you been stressed lately?"
```

#### Ending a Check-in

```
/end
```

You'll receive a summary of your health status.

### Medication Reminders

#### How It Works

1. **Scheduled Time** → Bot sends reminder
2. **Inline Buttons** → Tap "✓ Taken" or "⏭ Skip"
3. **If Skipped** → Choose reason (side effects, ran out, etc.)
4. **Caregiver Alerted** → If serious issue

#### Example Reminder

```
⏰ 8:00 AM — Time for your medicine:

💊 Metformin (500mg)
   Take with meals

[✓ Taken Metformin] [⏭ Skip Metformin]
```

### Health Alerts

#### Alert Levels

| Level | Trigger | Action |
|-------|---------|--------|
| 🟢 GREEN | Score < 15 | Continue monitoring |
| 🟡 YELLOW | Score 15-30 | Daily digest |
| 🟠 ORANGE | Score 30-50 | Instant notification |
| 🔴 RED | Score 50+ | Emergency alert |

#### Example Alert (to Caregiver)

```
🚨 Project AesculAI Alert

Patient: John
Level: ORANGE
Score: 35

Issues Detected:
• pain
• distress

Time: 09:45 on 13 Mar 2026
```

---

## 🌐 Web Dashboard (PWA)

**Status:** ⚠️ Partially Implemented (UI Complete, Not Yet Deployed)

### What's Currently Built

**Landing Page** - Basic homepage with feature overview  
**Chat Interface** - UI complete with demo AI responses (not connected to MERaLiON yet)  
**Dashboard** - UI complete with mock data (not connected to Supabase yet)  
**Patient List** - Basic display with mock patients

### What's Not Yet Implemented

- ❌ Not deployed to Vercel
- ❌ Using mock data (not connected to real database)
- ❌ No user authentication
- ❌ Chat not connected to MERaLiON API
- ❌ Not a PWA yet (no manifest/service worker)

### Future Plans

**Phase 1 (Planned):**
- Deploy to Vercel
- Connect to Supabase database
- Add Supabase Auth for login
- Connect chat to MERaLiON

**Phase 2 (Future):**
- Real-time alert updates
- Health trend graphs
- Report generation UI
- Push notifications
- PWA installation

### Access the Dashboard

**Local Development:**
```bash
cd ProjectIC/web
npm run dev
# Open http://localhost:3000
```

**Production:** Coming soon (will be deployed to Vercel)

---

## 🎙️ Alexa Skill

**Status:** 🚧 Designed but Not Yet Deployed (40% Complete)

### What's Ready

- ✅ Interaction model (intent schema, sample utterances)
- ✅ Backend handler code written
- ✅ MERaLiON integration code
- ✅ Conversation flow designed

### What's Not Yet Done

- ❌ Not uploaded to Alexa Developer Console
- ❌ Not deployed to Google Cloud Functions
- ❌ No account linking configured
- ❌ Not tested on Echo devices

### Future Plans

**Phase 1 (Planned):**
- Create skill in Alexa Developer Console
- Upload interaction model
- Deploy webhook to Cloud Functions
- Configure account linking with Telegram

**Phase 2 (Future):**
- Test on Echo devices
- Submit for certification
- Add voice-only medication reminders
- Multi-language support (Malay, Tamil)

### How It Will Work (When Deployed)

#### Setup (Future)

1. Open Alexa app on your phone
2. Go to "Skills & Games"
3. Search for "Aescul Helper"
4. Tap "Enable to Use"
5. Link your account (matches with Telegram)

#### Usage (Future)

**Say:**
> "Alexa, open Aescul Helper"

**Or:**
> "Alexa, ask Aescul Helper to check in"

#### Example Conversation (Future)

```
Alexa: "Hello! I'm Aescul Helper, your health companion. How are you feeling today?"

You: "I'm feeling tired"

Alexa: "Aiyo, tired ah? Did you sleep well last night, hor?"

You: "Not really, kept waking up"

Alexa: "Aiyah, sleep problem again. Have you been stressed lately?"
```

**Note:** The Alexa skill is designed and coded, but not yet deployed. It's planned for a future release after the Telegram bot and PWA are fully production-ready.

---

## 📋 Command Reference

### General Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `/start` | Begin a check-in session | Everyone |
| `/end` | Complete current check-in | Patients |
| `/status` | View current session status | Everyone |
| `/myrole` | View your current role(s) | Everyone |

### Registration Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `/registerpatient` | Register as a patient | Everyone |
| `/registercaseworker` | Register as a case worker | Everyone |

### Caregiver Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/assign` | Assign patient to yourself | `/assign John` |
| `/addmed` | Add medication | `/addmed John Metformin 500mg 08:00,20:00` |
| `/listmed` | List patient's medications | `/listmed John` |
| `/delmed` | Delete medication | `/delmed John Metformin` |
| `/adherence` | View medication adherence | `/adherence John` |
| `/weeklyreport` | Generate weekly report | `/weeklyreport John` |

### Medication Reminder Buttons

When you receive a medication reminder:

| Button | Action |
|--------|--------|
| ✓ Taken [Med] | Mark as taken |
| ⏭ Skip [Med] | Mark as skipped (shows reason options) |
| ✅ Taken All (N meds) | Mark all as taken |

**Skip Reasons:**
- ✅ Already took it → Marks as taken
- ⚠️ Side effects → Logs + alerts caregiver
- 👨‍⚕️ Doctor said pause → Logs only
- 💊 Ran out → Logs + alerts caregiver
- ❌ Don't need it → Logs only
- 🤷 No reason → Logs only

---

## ❓ FAQ

### General

**Q: What is Project AesculAI?**  
A: An AI-powered daily health check-in system for elderly patients living alone. It monitors health through natural conversations and alerts caregivers when needed.

**Q: Is it free?**  
A: Yes! Completely free to use.

**Q: What languages does it support?**  
A: Primarily English with Singlish/local context. Can understand code-switching.

### Telegram Bot

**Q: How often will the bot check in?**  
A: Twice daily - 8 AM (morning) and 2 PM (afternoon).

**Q: Can I start a check-in anytime?**  
A: Yes! Just say "Hello Aescul Helper" or send any message.

**Q: What happens if I mention concerning symptoms?**  
A: The bot calculates a risk score and alerts your caregiver if needed (score ≥ 30).

**Q: Can I be both a patient and a caregiver?**  
A: Yes! Just run both `/registerpatient` and `/registercaseworker`.

### Medication

**Q: How do I set up medication reminders?**  
A: Your caregiver uses `/addmed <patient> <med> <dosage> <times>` to set them up.

**Q: What if I miss a medication reminder?**  
A: The bot follows up after 30 minutes, then alerts your caregiver after 60 minutes.

**Q: Can I skip medications?**  
A: Yes, just tap "Skip" and choose a reason. Some reasons alert your caregiver.

### Privacy

**Q: Is my data private?**  
A: Yes. Conversations are encrypted and stored securely in Supabase. Only you and your assigned caregiver(s) can see your data.

**Q: Who receives my health alerts?**  
A: Only the caregiver you're assigned to (via `/assign` command).

---

## 🔧 Troubleshooting

### Bot Not Responding

**Problem:** Bot doesn't reply to messages

**Solutions:**
1. Check you're messaging @AesculAI_helper_bot
2. Make sure you've registered (`/registerpatient` or `/registercaseworker`)
3. Try `/start` to begin a new session
4. Check your internet connection

### Commands Not Working

**Problem:** Command returns error or not found

**Solutions:**
1. Check spelling (commands are case-sensitive)
2. Make sure you're registered in the right role
3. Some commands require arguments (e.g., `/assign John`)
4. Try `/myrole` to verify your registration

### Not Receiving Alerts (Caregiver)

**Problem:** Patient triggers high-risk but no alert received

**Solutions:**
1. Make sure you're registered as case worker (`/registercaseworker`)
2. Make sure patient is assigned to you (`/assign <patient>`)
3. Check patient's risk score reaches ≥ 30 (ORANGE) or ≥ 50 (RED)
4. Verify your Telegram notification settings

### Medication Reminders Not Coming

**Problem:** No reminders at scheduled times

**Solutions:**
1. Verify medications are added (`/listmed <patient>`)
2. Check reminder times are in 24-hour format (e.g., "08:00" not "8:00 AM")
3. Make sure bot is running (send any message to test)
4. Check timezone (all times in Singapore GMT+8)

### Alexa Skill Issues

**Problem:** "There was a problem with the requested skill's response"

**Solutions:**
1. Check your internet connection
2. Make sure the skill is enabled in Alexa app
3. Try: "Alexa, disable Aescul Helper" then "Alexa, enable Aescul Helper"
4. Check if your phone number is linked correctly

### Registration Issues

**Problem:** "Already registered" but can't use features

**Solutions:**
1. Check your role with `/myrole`
2. If registered as patient but need caregiver features, run `/registercaseworker`
3. If need to re-register, contact support to reset

---

## 🆘 Getting Help

### Support Channels

- 📱 **Telegram:** Message @AesculAI_helper_bot with your question
- 📧 **Email:** [Your support email]
- 📖 **Documentation:** This README

### Bug Reports

Found a bug? Please include:
1. What you were trying to do
2. What happened instead
3. Screenshot of the error
4. Your Telegram username

---

## 🎓 For Competition Judges

### Quick Test Guide

**5-Minute Test:**

1. **Register:** `/registerpatient` and `/registercaseworker`
2. **Assign Yourself:** `/assign <your_name>`
3. **Test Check-in:** Say "Hello Aescul Helper" → "I'm in pain"
4. **Test Medications:** `/addmed <your_name> VitaminC 1tab 08:00`
5. **View Reports:** `/adherence <your_name>` and `/weeklyreport <your_name>`

**Full Test (15 minutes):**

See `JUDGE_TESTING_GUIDE.md` for complete testing scenarios.

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **AI Singapore** - MERaLiON LLM for Singlish understanding
- **Supabase** - Database backend
- **Telegram** - Bot platform
- **Render** - Hosting

---

<div align="center">

**Made with ❤️ for elderly care in Singapore**

[Telegram Bot](https://t.me/AesculAI_helper_bot) • [Documentation](README.md) • [Support](mailto:support@example.com)

</div>
