# Project IC - API Documentation

## 📡 API Overview

Project IC provides RESTful APIs for the web dashboard and webhook endpoints for Telegram and Alexa integrations.

**Base URLs:**
- **Production Bot:** `https://project-ic-bot.onrender.com`
- **Production Web:** `https://project-ic.vercel.app`
- **Development:** `http://localhost:3000` (web), `http://localhost:8080` (bot)

---

## 🔐 Authentication

### Supabase Auth (Web Dashboard)

All web API requests require authentication via Supabase JWT token.

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Getting a Token:**
```javascript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})

const token = data.session.access_token
```

### Telegram Bot API

No authentication required. Requests come from Telegram's servers with bot token verification.

---

## 📋 Table of Contents

1. [Bot Server API](#bot-server-api)
2. [Web Dashboard API](#web-dashboard-api)
3. [Telegram Webhook](#telegram-webhook)
4. [Alexa Webhook](#alexa-webhook)
5. [Error Handling](#error-handling)

---

## 🤖 Bot Server API

### Health Check

**Endpoint:** `GET /health`

**Description:** Check bot server status

**Response:**
```json
{
  "status": "ok",
  "service": "project-ic-bot",
  "version": "1.0.0",
  "uptime": 86400,
  "patients_registered": 15
}
```

---

### Chat Proxy (PWA → MERaLiON)

**Endpoint:** `POST /api/chat`

**Description:** Proxy chat requests from PWA to MERaLiON API (avoids CORS)

**Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "I'm feeling tired today"}
  ],
  "patient_id": "telegram-123",
  "session_type": "morning"
}
```

**Response:**
```json
{
  "response": "Aiyo, tired ah? Did you sleep well last night?",
  "risk_score": 5,
  "signals": ["fatigue"],
  "timestamp": "2026-03-13T08:30:00+08:00"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid request body
- `500 Internal Server Error` - MERaLiON API error

---

## 🌐 Web Dashboard API

### Patients

#### List All Patients

**Endpoint:** `GET /api/patients`

**Headers:**
```http
Authorization: Bearer {token}
```

**Query Parameters:**
- `active` (boolean): Filter active patients
- `case_worker_id` (string): Filter by case worker

**Response:**
```json
{
  "patients": [
    {
      "id": "uuid-123",
      "name": "John Doe",
      "preferred_name": "John",
      "telegram_id": "123456789",
      "conditions": ["diabetes", "hypertension"],
      "case_worker_id": "987654321",
      "is_active": true,
      "last_checkin": "2026-03-13T08:00:00+08:00",
      "risk_level": "GREEN",
      "created_at": "2026-01-15T10:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 20
}
```

---

#### Get Single Patient

**Endpoint:** `GET /api/patients/{patient_id}`

**Response:**
```json
{
  "id": "uuid-123",
  "name": "John Doe",
  "telegram_id": "123456789",
  "conditions": ["diabetes"],
  "medications": [
    {
      "id": "med-123",
      "name": "Metformin",
      "dosage": "500mg",
      "adherence_rate": 95.5
    }
  ],
  "stats": {
    "checkins_this_week": 14,
    "avg_risk_score": 12,
    "alerts_this_month": 2
  }
}
```

---

#### Create Patient

**Endpoint:** `POST /api/patients`

**Request Body:**
```json
{
  "name": "John Doe",
  "telegram_id": "123456789",
  "preferred_name": "John",
  "conditions": ["diabetes"],
  "case_worker_id": "987654321"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid-new",
  "name": "John Doe",
  "message": "Patient created successfully"
}
```

---

#### Update Patient

**Endpoint:** `PATCH /api/patients/{patient_id}`

**Request Body:**
```json
{
  "preferred_name": "Johnny",
  "conditions": ["diabetes", "hypertension"]
}
```

**Response:** `200 OK`

---

#### Delete Patient

**Endpoint:** `DELETE /api/patients/{patient_id}`

**Response:** `204 No Content`

---

### Alerts

#### List Alerts

**Endpoint:** `GET /api/alerts`

**Query Parameters:**
- `resolved` (boolean): Filter resolved/unresolved
- `risk_level` (string): Filter by level (YELLOW/ORANGE/RED)
- `patient_id` (string): Filter by patient
- `limit` (number): Max results (default: 20)

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert-123",
      "patient_id": "uuid-123",
      "patient_name": "John Doe",
      "risk_level": "ORANGE",
      "risk_score": 35,
      "title": "Health Concern Detected",
      "signals": ["pain", "distress"],
      "resolved": false,
      "created_at": "2026-03-13T09:45:00+08:00",
      "resolved_at": null
    }
  ],
  "total": 5,
  "unresolved": 2
}
```

---

#### Create Alert

**Endpoint:** `POST /api/alerts`

**Request Body:**
```json
{
  "patient_id": "uuid-123",
  "risk_level": "ORANGE",
  "risk_score": 35,
  "title": "Health Concern Detected",
  "signals": ["pain", "distress"],
  "notes": "Patient mentioned knee pain and feeling lonely"
}
```

**Response:** `201 Created`

---

#### Resolve Alert

**Endpoint:** `PATCH /api/alerts/{alert_id}/resolve`

**Request Body:**
```json
{
  "resolution_notes": "Called patient, referred to doctor"
}
```

**Response:** `200 OK`

---

### Check-ins

#### List Check-ins

**Endpoint:** `GET /api/checkins`

**Query Parameters:**
- `patient_id` (string): Filter by patient
- `start_date` (date): From date (YYYY-MM-DD)
- `end_date` (date): To date (YYYY-MM-DD)
- `session_type` (string): morning/afternoon/evening

**Response:**
```json
{
  "checkins": [
    {
      "id": "checkin-123",
      "patient_id": "uuid-123",
      "patient_name": "John Doe",
      "session_type": "morning",
      "started_at": "2026-03-13T08:00:00+08:00",
      "ended_at": "2026-03-13T08:05:00+08:00",
      "risk_score": 12,
      "risk_level": "GREEN",
      "signals_detected": ["fatigue"],
      "message_count": 6,
      "transcript": [
        {
          "role": "bot",
          "content": "Good morning! How did you sleep?",
          "timestamp": "2026-03-13T08:00:00+08:00"
        },
        {
          "role": "user",
          "content": "Not too bad, a bit tired",
          "timestamp": "2026-03-13T08:00:15+08:00"
        }
      ]
    }
  ]
}
```

---

#### Get Check-in Details

**Endpoint:** `GET /api/checkins/{checkin_id}`

**Response:** Full check-in object with complete transcript

---

### Medications

#### List Medications

**Endpoint:** `GET /api/medications`

**Query Parameters:**
- `patient_id` (string): Filter by patient
- `active` (boolean): Filter active medications

**Response:**
```json
{
  "medications": [
    {
      "id": "med-123",
      "patient_id": "telegram-123",
      "name": "Metformin",
      "dosage": "500mg",
      "instructions": "Take with meals",
      "reminder_times": ["08:00", "20:00"],
      "active": true,
      "adherence": {
        "total_doses": 60,
        "taken": 57,
        "skipped": 3,
        "missed": 0,
        "adherence_rate": 95.0
      },
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

#### Create Medication

**Endpoint:** `POST /api/medications`

**Request Body:**
```json
{
  "patient_id": "telegram-123",
  "name": "Vitamin C",
  "dosage": "1 tablet",
  "instructions": "Take after breakfast",
  "reminder_times": ["08:00"],
  "created_by": "telegram-456"
}
```

**Response:** `201 Created`

---

#### Update Medication

**Endpoint:** `PATCH /api/medications/{medication_id}`

**Request Body:**
```json
{
  "reminder_times": ["08:00", "14:00"],
  "instructions": "Take with food"
}
```

---

#### Delete Medication

**Endpoint:** `DELETE /api/medications/{medication_id}`

**Response:** `204 No Content`

---

### Reports

#### Generate Weekly Report

**Endpoint:** `POST /api/reports/weekly`

**Request Body:**
```json
{
  "patient_id": "telegram-123",
  "start_date": "2026-03-06",
  "end_date": "2026-03-12"
}
```

**Response:**
```json
{
  "report_id": "report-123",
  "patient_name": "John Doe",
  "period": {
    "start": "2026-03-06",
    "end": "2026-03-12"
  },
  "summary": {
    "checkins_completed": 12,
    "avg_risk_score": 15,
    "max_risk_score": 28,
    "alerts_generated": 1
  },
  "health_signals": {
    "pain": 3,
    "fatigue": 5,
    "distress": 1,
    "cognitive": 0
  },
  "medication_adherence": {
    "rate": 95.0,
    "missed_doses": 2,
    "skip_reasons": {
      "side_effects": 1,
      "ran_out": 1
    }
  },
  "recommendations": [
    "Continue monitoring fatigue levels",
    "Consider follow-up for side effects mentioned"
  ],
  "generated_at": "2026-03-13T10:00:00+08:00"
}
```

---

## 📱 Telegram Webhook

### Webhook Endpoint

**Endpoint:** `POST /webhook/telegram`

**Description:** Receives updates from Telegram Bot API

**Headers:**
```http
Content-Type: application/json
X-Telegram-Bot-Api-Secret-Token: {secret}
```

**Request Body (Message):**
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {
      "id": 123456789,
      "first_name": "John",
      "username": "johndoe"
    },
    "chat": {
      "id": 123456789,
      "type": "private"
    },
    "text": "I'm feeling tired today"
  }
}
```

**Request Body (Callback Query):**
```json
{
  "update_id": 123456790,
  "callback_query": {
    "id": "callback-123",
    "from": {
      "id": 123456789
    },
    "message": {
      "message_id": 100,
      "chat": {
        "id": 123456789
      }
    },
    "data": "med_taken:123456789:med-123:20260313:0800"
    }
}
```

**Response:** `200 OK` (empty body)

**Bot Actions:**
1. Processes update
2. Sends response message
3. Updates database
4. Triggers alerts if needed

---

## 🎙️ Alexa Webhook

### Alexa Endpoint

**Endpoint:** `POST /webhook/alexa` (GCP Cloud Functions)

**Description:** Handles Alexa skill requests

**Request Body (Launch):**
```json
{
  "version": "1.0",
  "session": {
    "new": true,
    "sessionId": "amzn1.echo-api.session.123",
    "user": {
      "userId": "amzn1.ask.account.123"
    }
  },
  "request": {
    "type": "LaunchRequest",
    "requestId": "amzn1.echo-api.request.123",
    "timestamp": "2026-03-13T08:00:00Z",
    "locale": "en-US"
  }
}
```

**Request Body (Intent):**
```json
{
  "version": "1.0",
  "session": {
    "new": false,
    "sessionId": "amzn1.echo-api.session.123"
  },
  "request": {
    "type": "IntentRequest",
    "intent": {
      "name": "CheckIn",
      "slots": {
        "Response": {
          "name": "Response",
          "value": "I'm feeling tired"
        }
      }
    }
  }
}
```

**Response:**
```json
{
  "version": "1.0",
  "response": {
    "outputSpeech": {
      "type": "PlainText",
      "text": "Aiyo, tired ah? Did you sleep well last night?"
    },
    "shouldEndSession": false,
    "reprompt": {
      "outputSpeech": {
        "type": "PlainText",
        "text": "How are you feeling today?"
      }
    }
  }
}
```

---

## ⚠️ Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "patient_id",
      "reason": "Patient not found"
    }
  },
  "timestamp": "2026-03-13T10:00:00+08:00",
  "request_id": "req-123"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMIT` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | External service down |

---

## 📊 Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/chat` | 60 requests | 1 minute |
| `/api/alerts` | 100 requests | 1 minute |
| `/api/patients` | 200 requests | 1 minute |
| `/webhook/telegram` | 30 requests | 1 second |

---

## 📝 Request/Response Examples

### Example: Complete Check-in Flow

**1. Patient sends message (via webhook)**
```json
POST /webhook/telegram
{
  "message": {
    "from": {"id": "123"},
    "text": "I'm feeling very sad today"
  }
}
```

**2. Bot analyzes and responds**
```json
Response: 200 OK
(Bot sends message via Telegram API)
{
  "chat_id": "123",
  "text": "I'm sorry to hear that. What's making you feel sad?"
}
```

**3. Alert created (if needed)**
```json
POST /api/alerts (internal)
{
  "patient_id": "123",
  "risk_level": "ORANGE",
  "risk_score": 35,
  "signals": ["distress"]
}
```

**4. Case worker views alert**
```json
GET /api/alerts?resolved=false
{
  "alerts": [...]
}
```

---

## 🔧 Testing

### Test Endpoints

**Health Check:**
```bash
curl https://project-ic-bot.onrender.com/health
```

**Create Test Patient:**
```bash
curl -X POST https://project-ic.vercel.app/api/patients \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Patient","telegram_id":"999"}'
```

**Send Chat Message:**
```bash
curl -X POST https://project-ic-bot.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages":[{"role":"user","content":"Hello"}],
    "patient_id":"999"
  }'
```

---

## 📚 Related Documentation

- [Architecture](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [User Guide](README.md)

---

*Last updated: 2026-03-13*
