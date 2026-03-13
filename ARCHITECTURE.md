# Project IC - System Architecture

## 📐 Overview

Project IC is a multi-platform AI-powered health monitoring system for elderly patients. It uses a microservices architecture with loose coupling between components.

---

## 🏗️ High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
├───────────────────┬──────────────────┬─────────────────────────┤
│  Telegram Bot     │   Web PWA        │   Alexa Skill           │
│  (Patient/CW)     │   (Dashboard)    │   (Voice Interface)     │
└─────────┬─────────┴────────┬─────────┴────────────┬────────────┘
          │                  │                      │
          ▼                  ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                          │
├───────────────────┬──────────────────┬─────────────────────────┤
│ Telegram Bot API  │  Next.js API     │  Alexa webhook          │
│ (Render)          │  (Vercel)        │  (GCP Functions)        │
└─────────┬─────────┴────────┬─────────┴────────────┬────────────┘
          │                  │                      │
          └──────────────────┼──────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│  Core Services:                                                 │
│  • Check-in Engine (conversations, risk scoring)               │
│  • Medication Manager (reminders, tracking)                    │
│  • Alert System (escalation, notifications)                    │
│  • Report Generator (weekly summaries)                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   AI Layer   │ │   Database   │ │  Storage     │
├──────────────┤ ├──────────────┤ ├──────────────┤
│ MERaLiON API │ │  Supabase    │ │ Local Files  │
│ (AI Singapore)│ │  (PostgreSQL)│ │ (JSON configs)│
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 🧩 Component Details

### 1. Client Layer

#### Telegram Bot
- **Purpose:** Primary user interface
- **Technology:** Python, python-telegram-bot
- **Features:**
  - Text and voice conversations
  - Inline buttons for medication
  - Command handlers
  - Callback queries

#### Web PWA (Progressive Web App)
- **Purpose:** Dashboard for caregivers
- **Technology:** Next.js 14, React, TypeScript
- **Features:**
  - Patient overview
  - Alert management
  - Medication tracking
  - Health reports
  - Mobile-responsive

#### Alexa Skill
- **Purpose:** Voice-first interface
- **Technology:** Alexa Skills Kit, Cloud Functions
- **Features:**
  - Voice interactions
  - Session management
  - Integration with bot backend

---

### 2. API Gateway Layer

#### Telegram Bot Server (Render)
- **URL:** `https://project-ic-bot.onrender.com`
- **Technology:** Python, aiohttp
- **Endpoints:**
  - `/webhook/telegram` - Telegram updates
  - `/api/chat` - PWA chat proxy
  - `/health` - Health check

#### Next.js API (Vercel)
- **URL:** `https://project-ic.vercel.app`
- **Endpoints:**
  - `/api/alert` - Create/retrieve alerts
  - `/api/patients` - Patient CRUD
  - `/api/checkins` - Check-in history
  - `/api/reports` - Generate reports

#### Alexa Webhook (Cloud Functions)
- **URL:** `https://asia-southeast1-aesculai.cloudfunctions.net/project-ic-webhook`
- **Purpose:** Handle Alexa requests

---

### 3. Business Logic Layer

#### Core Modules

**Check-in Engine** (`telegram_voice_bot.py`, `checkin_bot.py`)
```python
Responsibilities:
- Session management
- Conversation flow
- Risk scoring
- Alert triggering

Key Components:
- analyze_response() - Signal detection
- generate_response() - AI conversation
- send_case_worker_alert() - Alert system
```

**Medication Manager** (`medication_reminder.py`)
```python
Responsibilities:
- Medication CRUD
- Reminder scheduling
- Adherence tracking
- Escalation logic

Key Components:
- send_reminder() - Send medication reminders
- handle_callback() - Button interactions
- get_adherence_report() - Compliance stats
```

**Alert System**
```python
Responsibilities:
- Risk level calculation
- Alert routing
- Escalation rules
- Notification delivery

Alert Levels:
- GREEN (0-15): Continue monitoring
- YELLOW (15-30): Daily digest
- ORANGE (30-50): Instant alert
- RED (50+): Emergency
```

**Report Generator** (`scheduler.py`)
```python
Responsibilities:
- Weekly health summaries
- Data aggregation
- Report formatting
- Email delivery (via Resend)
```

---

### 4. AI Layer

#### MERaLiON API

**Provider:** AI Singapore
**Models:**
- `MERaLiON/MERaLiON-3-10B` - Text conversations
- `MERaLiON/MERaLiON-2-10B-ASR` - Speech recognition

**Capabilities:**
- Singlish understanding
- Code-switching support
- Empathetic responses
- Context-aware conversations

**API Endpoints:**
```
POST http://meralion.org:8010/v1/chat/completions
Headers: Authorization: Bearer {API_KEY}
Body: {
  "model": "MERaLiON/MERaLiON-3-10B",
  "messages": [...]
}
```

---

### 5. Database Layer

#### Supabase (PostgreSQL)

**Tables:**

**`patients`**
```sql
- id (UUID)
- name (TEXT)
- telegram_id (TEXT, unique)
- preferred_name (TEXT)
- conditions (TEXT[])
- medications (TEXT[])
- case_worker_id (TEXT)
- is_active (BOOLEAN)
- created_at (TIMESTAMPTZ)
```

**`alerts`**
```sql
- id (UUID)
- patient_id (UUID, FK)
- risk_level (TEXT)
- title (TEXT)
- signals (TEXT[])
- resolved (BOOLEAN)
- created_at (TIMESTAMPTZ)
```

**`checkins`**
```sql
- id (UUID)
- patient_id (UUID, FK)
- session_type (TEXT)
- started_at (TIMESTAMPTZ)
- ended_at (TIMESTAMPTZ)
- risk_score (INT)
- risk_level (TEXT)
- transcript (JSONB)
```

**`medications`**
```sql
- id (UUID)
- patient_id (TEXT)
- name (TEXT)
- dosage (TEXT)
- instructions (TEXT)
- reminder_times (TEXT[])
- active (BOOLEAN)
- created_at (TIMESTAMPTZ)
```

**`medication_reminders`**
```sql
- id (UUID)
- medication_id (UUID, FK)
- patient_id (TEXT)
- scheduled_date (DATE)
- scheduled_time (TEXT)
- status (TEXT) -- pending/taken/skipped/missed
- skip_reason (TEXT)
- reminder_sent_at (TIMESTAMPTZ)
- responded_at (TIMESTAMPTZ)
```

#### Local File Storage

**`config/patients.json`**
```json
{
  "patients": [
    {
      "id": "telegram-123",
      "name": "John",
      "telegram_id": "123",
      "case_worker_id": "456"
    }
  ]
}
```

**`config/medications.json`**
```json
{
  "medications": [
    {
      "id": "med-123",
      "patient_id": "123",
      "name": "Metformin",
      "dosage": "500mg",
      "reminder_times": ["08:00", "20:00"]
    }
  ]
}
```

---

## 🔄 Data Flow

### 1. Check-in Flow

```
1. Patient sends message
   ↓
2. Bot receives via Telegram API
   ↓
3. Message analyzed (signal detection)
   ↓
4. Risk score calculated
   ↓
5. AI generates response (MERaLiON)
   ↓
6. Response sent to patient
   ↓
7. If score ≥ 30:
   - Alert created in database
   - Notification sent to caregiver
   ↓
8. Check-in saved to database
```

### 2. Medication Reminder Flow

```
1. Scheduler triggers at scheduled time
   ↓
2. Bot sends reminder with inline buttons
   ↓
3. Patient taps button (Taken/Skip)
   ↓
4. Bot updates reminder status
   ↓
5. If skipped with "ran_out" or "side_effects":
   - Alert sent to caregiver
   ↓
6. Adherence stats updated
```

### 3. Alert Escalation Flow

```
Patient message detected
   ↓
Risk score: 35 (ORANGE)
   ↓
Alert created in DB
   ↓
Notification sent to case_worker_id
   ↓
Case worker views alert
   ↓
Case worker marks as resolved
   ↓
Alert status updated
```

---

## 🔐 Security Architecture

### Authentication

**Telegram Bot:**
- No explicit authentication
- Users identified by Telegram ID
- Role-based access control (patient/case_worker)

**Web Dashboard:**
- Supabase Auth (email/password)
- Session tokens
- Row-level security (RLS)

**Alexa:**
- Account linking via phone number
- Matches with Telegram user

### Data Privacy

**Encryption:**
- In transit: HTTPS/TLS
- At rest: Supabase encryption

**Access Control:**
- Patients see only their own data
- Case workers see assigned patients only
- Admins see all data

**Data Retention:**
- Check-ins: 90 days
- Alerts: 180 days
- Medication logs: 365 days

---

## 📊 Scalability

### Current Architecture (Free Tier)

| Component | Capacity | Cost |
|-----------|----------|------|
| Render | 750 hours/month | $0 |
| Vercel | 100GB bandwidth | $0 |
| Supabase | 500MB database | $0 |
| MERaLiON | Free access | $0 |

**Estimated Capacity:** 50-100 patients

### Scaling Strategy

**To 1,000 Patients:**
- Upgrade Render: $7/month (Starter)
- Upgrade Supabase: $25/month (Pro)
- Add caching (Redis): $5/month

**To 10,000 Patients:**
- Dedicated server: $50/month
- Database: $75/month
- Load balancer: $20/month
- CDN: $20/month

---

## 🌍 Deployment Architecture

### Production Environment

```
┌─────────────────────────────────────┐
│         PRODUCTION                  │
├─────────────────────────────────────┤
│                                     │
│  Bot Server (Render)                │
│  https://project-ic-bot.onrender.com│
│                                     │
│  Web Dashboard (Vercel)             │
│  https://project-ic.vercel.app      │
│                                     │
│  Database (Supabase)                │
│  https://xhonx.supabase.co          │
│                                     │
│  Alexa (Cloud Functions)            │
│  asia-southeast1                    │
│                                     │
└─────────────────────────────────────┘
```

### Development Environment

```
┌─────────────────────────────────────┐
│         DEVELOPMENT                 │
├─────────────────────────────────────┤
│                                     │
│  Bot: localhost:8080                │
│  Web: localhost:3000                │
│  DB: Local Supabase instance        │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔧 Technology Stack

### Backend
- **Language:** Python 3.11
- **Framework:** python-telegram-bot, aiohttp
- **AI:** MERaLiON API
- **Database:** Supabase (PostgreSQL)
- **Hosting:** Render

### Frontend
- **Language:** TypeScript
- **Framework:** Next.js 14, React 18
- **Styling:** Tailwind CSS
- **Hosting:** Vercel

### Integrations
- **Telegram:** Bot API
- **Alexa:** Alexa Skills Kit
- **Email:** Resend
- **Voice:** MERaLiON ASR

---

## 📈 Monitoring & Logging

### Application Logs
```python
# Render logs
https://dashboard.render.com

# Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Key Metrics
- Response time: < 3 seconds
- Uptime: > 99%
- Error rate: < 1%
- Alert delivery: > 95%

### Alerting
- Server down: Email to admin
- API errors: Telegram to developer
- High error rate: SMS to on-call

---

## 🚀 Future Architecture

### Planned Enhancements

**Phase 2:**
- Add Redis caching
- Implement message queue (BullMQ)
- Add analytics dashboard
- Multi-language support

**Phase 3:**
- Microservices split
- Kubernetes deployment
- Real-time WebSocket updates
- ML model for risk prediction

**Phase 4:**
- Integration with MOH systems
- IoT device support
- Telemedicine integration
- Hospital discharge workflow

---

## 📚 Related Documentation

- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [User Guide](README.md)

---

*Last updated: 2026-03-13*
