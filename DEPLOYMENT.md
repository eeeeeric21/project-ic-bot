# Project IC - Deployment Guide

Complete deployment guide for Project IC elderly care system.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Deploy](#quick-deploy)
- [Manual Deployment](#manual-deployment)
- [Database Setup](#database-setup)
- [Telegram Bot Configuration](#telegram-bot-configuration)
- [Email Setup](#email-setup)
- [Local Development](#local-development)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring](#monitoring)
- [Security Checklist](#security-checklist)
- [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### Required Accounts

| Service | Purpose | Free Tier | Link |
|---------|---------|-----------|------|
| GitHub | Code repository | Unlimited | [github.com](https://github.com) |
| Telegram | Bot platform | Unlimited | [telegram.org](https://telegram.org) |
| Supabase | Database | 500MB | [supabase.com](https://supabase.com) |
| Render | Bot hosting | 750 hrs/month | [render.com](https://render.com) |
| Vercel | Web hosting | 100GB/month | [vercel.com](https://vercel.com) |
| AI Singapore | MERaLiON API | Free access | [aisingapore.org](https://aisingapore.org) |

### Required Tools

```bash
# Git
git --version

# Python 3.11+
python --version

# Node.js 18+
node --version

# npm
npm --version
```

---

## 🚀 Quick Deploy (5 minutes)

### Step 1: Clone & Push to GitHub

```bash
# Clone repository
git clone https://github.com/eeeeeric21/project-ic-bot.git
cd project-ic-bot

# Push to your GitHub
git remote set-url origin https://github.com/YOUR_USERNAME/project-ic-bot.git
git push -u origin main
```

### Step 2: Create Telegram Bot

1. Open Telegram, search `@BotFather`
2. Send `/newbot`
3. Follow prompts:
   - Name: `Project IC Bot`
   - Username: `your_project_ic_bot`
4. **Save the token** (format: `1234567890:ABCdef...`)

### Step 3: Get Your Chat ID

```bash
# Message your bot first, then:
curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
# Look for "chat":{"id":123456789
```

### Step 4: Setup Supabase Database

1. Go to [supabase.com](https://supabase.com) → New Project
2. Name: `project-ic`
3. Region: **Southeast Asia (Singapore)**
4. Wait 2 minutes for setup
5. Go to SQL Editor
6. Copy/paste contents of `database/schema.sql`
7. Click "Run"
8. Save:
   - `SUPABASE_URL` (from Settings → API)
   - `SUPABASE_ANON_KEY` (from Settings → API)

### Step 5: Deploy Bot to Render

1. Go to [render.com](https://render.com) → New → Web Service
2. Connect GitHub repo
3. Configure:
   ```
   Name: project-ic-bot
   Region: Singapore
   Branch: main
   Root Directory: . (leave empty)
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python scripts/bot_server.py
   ```
4. Add environment variables:
   ```
   TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
   TELEGRAM_CASE_WORKER_CHAT_ID=your_chat_id
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGci...
   MERALION_API_URL=http://meralion.org:8010/v1
   MERALION_API_KEY=your_key
   MERALION_MODEL=MERaLiON/MERaLiON-3-10B
   ```
5. Click "Create Web Service"
6. Wait 5-10 minutes

✅ **Bot deployed!** Test: Send `/start` to your bot in Telegram.

### Step 6: Deploy Web Dashboard to Vercel

1. Go to [vercel.com](https://vercel.com) → Add New Project
2. Import GitHub repo
3. Configure:
   ```
   Framework Preset: Next.js
   Root Directory: ProjectIC/web
   ```
4. Add environment variables:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
   ```
5. Click "Deploy"
6. Wait 2-3 minutes

✅ **Web dashboard deployed!** Visit your Vercel URL.

---

## 🔧 Manual Deployment

### Bot Server (Render)

#### Via Dashboard

1. Create account at [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect GitHub repository
4. Settings:
   ```
   Name: project-ic-bot
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python scripts/bot_server.py
   Instance Type: Free
   ```
5. Environment Variables:
   ```
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CASE_WORKER_CHAT_ID=your_id
   SUPABASE_URL=your_url
   SUPABASE_ANON_KEY=your_key
   MERALION_API_URL=http://meralion.org:8010/v1
   MERALION_API_KEY=your_key
   MERALION_MODEL=MERaLiON/MERaLiON-3-10B
   ```
6. Click "Create Web Service"

#### Via CLI

```bash
# Install Render CLI
brew tap render-oss/render
brew install render

# Login
render login

# Deploy
render services:create \
  --name project-ic-bot \
  --type web \
  --env python \
  --region singapore \
  --branch main \
  --buildCommand "pip install -r requirements.txt" \
  --startCommand "python scripts/bot_server.py"
```

---

### Web Dashboard (Vercel)

#### Via Dashboard

1. Import GitHub repository
2. Configure:
   - Framework: Next.js
   - Root Directory: `ProjectIC/web`
3. Environment Variables:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key
   ```
4. Deploy

#### Via CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd ProjectIC/web
vercel --prod

# Follow prompts, set environment variables
```

---

## 💾 Database Setup

### Supabase Configuration

#### 1. Create Project

1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Settings:
   ```
   Name: project-ic
   Database Password: [save this!]
   Region: Southeast Asia (Singapore)
   ```
4. Wait ~2 minutes

#### 2. Get Credentials

Go to Settings → API:
- `SUPABASE_URL`: Project URL
- `SUPABASE_ANON_KEY`: anon/public key

#### 3. Run Schema Migration

1. Go to SQL Editor
2. Paste contents of `database/schema.sql`:

```sql
-- Patients table
CREATE TABLE patients (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    telegram_id TEXT UNIQUE,
    preferred_name TEXT,
    conditions TEXT[],
    medications TEXT[],
    case_worker_id TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts table
CREATE TABLE alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id UUID REFERENCES patients(id),
    risk_level TEXT NOT NULL,
    risk_score INT,
    title TEXT,
    signals TEXT[],
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Check-ins table
CREATE TABLE checkins (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id UUID REFERENCES patients(id),
    session_type TEXT,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    risk_score INT,
    risk_level TEXT,
    signals TEXT[],
    transcript JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Medications table
CREATE TABLE medications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id TEXT NOT NULL,
    name TEXT NOT NULL,
    dosage TEXT,
    instructions TEXT,
    reminder_times TEXT[],
    active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Medication reminders table
CREATE TABLE medication_reminders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    medication_id UUID REFERENCES medications(id),
    patient_id TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    skip_reason TEXT,
    reminder_sent_at TIMESTAMPTZ,
    responded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_patients_telegram ON patients(telegram_id);
CREATE INDEX idx_alerts_patient ON alerts(patient_id);
CREATE INDEX idx_alerts_resolved ON alerts(resolved);
CREATE INDEX idx_checkins_patient ON checkins(patient_id);
CREATE INDEX idx_reminders_patient ON medication_reminders(patient_id);
CREATE INDEX idx_reminders_date ON medication_reminders(scheduled_date);

-- Enable Row Level Security
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkins ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_reminders ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for demo - tighten for production)
CREATE POLICY "Allow all access" ON patients FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON alerts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON checkins FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON medications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON medication_reminders FOR ALL USING (true) WITH CHECK (true);
```

3. Click "Run"

#### 4. (Optional) Add Demo Data

```sql
-- Insert demo patients
INSERT INTO patients (name, telegram_id, preferred_name, conditions)
VALUES
    ('Uncle Tan', '123456789', 'Uncle Tan', ARRAY['diabetes', 'hypertension']),
    ('Auntie Mary', '987654321', 'Auntie Mary', ARRAY['arthritis']);

-- Insert demo medications
INSERT INTO medications (patient_id, name, dosage, reminder_times)
VALUES
    ('123456789', 'Metformin', '500mg', ARRAY['08:00', '20:00']),
    ('123456789', 'Lisinopril', '10mg', ARRAY['08:00']);
```

---

## 🤖 Telegram Bot Configuration

### Create Bot

1. Open Telegram
2. Search `@BotFather`
3. Send `/newbot`
4. Follow prompts:
   - Bot name: `Project IC Bot`
   - Bot username: `project_ic_bot` (must end in `bot`)
5. Save the token

### Get Chat ID

**Method 1: API**
```bash
# Message your bot first
curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates

# Look for: "chat":{"id":123456789
```

**Method 2: Userbot**
```bash
# Use @userinfobot in Telegram
# It will show your ID
```

### Set Webhook (Production)

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -d "url=https://your-bot.onrender.com/webhook/telegram"
```

### Bot Commands (Set in BotFather)

Send to @BotFather:
```
/setcommands

start - Register and begin check-in
end - Complete current check-in
status - View your health status
registerpatient - Register as patient
registercaseworker - Register as caregiver
myrole - View your current role
assign - Assign patient to yourself
addmed - Add medication for patient
listmed - List patient's medications
delmed - Delete medication
adherence - View medication adherence
weeklyreport - Generate weekly report
```

---

## 📧 Email Setup (Optional)

### Resend Configuration

For sending weekly reports and alerts via email.

1. Create account at [resend.com](https://resend.com)
2. Get API key (starts with `re_`)
3. Add to environment:
   ```
   RESEND_API_KEY=re_xxxxxxxxxx
   ALERT_FROM_EMAIL=onboarding@resend.dev
   ```
4. For production: Verify your domain

**Test Email:**
```bash
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer re_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "onboarding@resend.dev",
    "to": "your@email.com",
    "subject": "Test from Project IC",
    "html": "<p>Test email</p>"
  }'
```

---

## 💻 Local Development

### Setup

```bash
# Clone repo
git clone https://github.com/eeeeeric21/project-ic-bot.git
cd project-ic-bot

# Backend (Python)
cd skills/project-ic-checkin
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Frontend (Node.js)
cd ../../../ProjectIC/web
npm install

# Create .env.local
cp .env.example .env.local
# Edit .env.local with your credentials
```

### Run Locally

**Backend:**
```bash
cd skills/project-ic-checkin
source venv/bin/activate
python scripts/telegram_voice_bot.py
```

**Frontend:**
```bash
cd ProjectIC/web
npm run dev
# Open http://localhost:3000
```

### Test Database Connection

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link project
supabase link --project-ref your-project-ref

# Test query
supabase db query "SELECT * FROM patients LIMIT 5"
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-bot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Render
        run: |
          curl ${{ secrets.RENDER_DEPLOY_HOOK }}
  
  deploy-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        run: |
          npm install -g vercel
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

### Render Deploy Hook

1. Go to Render Dashboard → Settings
2. Copy "Deploy Hook URL"
3. Add to GitHub Secrets as `RENDER_DEPLOY_HOOK`

### Vercel Integration

Vercel automatically deploys on push to main branch.

---

## 📊 Monitoring

### Health Check Endpoint

```bash
# Bot server health
curl https://your-bot.onrender.com/health

# Expected response:
{
  "status": "ok",
  "service": "project-ic-bot",
  "uptime": 86400,
  "patients_registered": 5
}
```

### Render Logs

```bash
# Via CLI
render logs project-ic-bot

# Via Dashboard
https://dashboard.render.com/web/srv-xxx/logs
```

### Vercel Analytics

```
https://vercel.com/dashboard → Project → Analytics
```

### Supabase Dashboard

```
https://supabase.com/dashboard/project/xxx
```

Monitor:
- Database size
- API requests
- Real-time connections

---

## 🔒 Security Checklist

Before going to production:

- [ ] **Environment variables** - All secrets in .env, not in code
- [ ] **HTTPS only** - All endpoints use HTTPS
- [ ] **Database security** - RLS policies enabled
- [ ] **Bot token** - Kept secret, rotated if leaked
- [ ] **Input validation** - All user inputs sanitized
- [ ] **Rate limiting** - Prevent abuse
- [ ] **Error handling** - Don't expose internals
- [ ] **Updates** - Regular dependency updates
- [ ] **Backups** - Database backup enabled
- [ ] **Monitoring** - Alerts for downtime

### Tighten Supabase Security

For production, replace permissive policies:

```sql
-- Patients: Users can only see their own data
CREATE POLICY "Users see own data" ON patients
  FOR SELECT USING (telegram_id = current_setting('request.jwt.claims')->>'telegram_id');

-- Case workers: Can see assigned patients
CREATE POLICY "Case workers see assigned" ON patients
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM case_workers
      WHERE case_workers.telegram_id = current_setting('request.jwt.claims')->>'telegram_id'
      AND case_workers.patients @> ARRAY[patients.telegram_id]
    )
  );
```

---

## 🐛 Troubleshooting

### Bot Not Responding

**Check:**
1. Is Render service running?
   ```bash
   curl https://your-bot.onrender.com/health
   ```
2. Are environment variables correct?
3. Is bot token valid?
4. Check Render logs

**Solution:**
```bash
# Restart service
render services:restart project-ic-bot

# Check logs
render logs project-ic-bot
```

---

### Database Connection Failed

**Check:**
1. Supabase project is active
2. URL format correct: `https://xxx.supabase.co`
3. Key starts with `eyJ`
4. IP whitelist (Settings → API → IP whitelist)

**Test:**
```bash
curl https://xxx.supabase.co/rest/v1/patients \
  -H "apikey: YOUR_ANON_KEY"
```

---

### Web Dashboard Not Loading

**Check:**
1. Environment variables in Vercel
2. Build succeeded
3. Browser console errors

**Solution:**
```bash
# Redeploy
vercel --prod

# Check build logs
https://vercel.com/dashboard
```

---

### MERaLiON API Errors

**Check:**
1. API URL correct
2. API key valid
3. Model name correct

**Test:**
```bash
curl -X POST http://meralion.org:8010/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MERaLiON/MERaLiON-3-10B",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

## 📚 Additional Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API.md)
- [User Guide](README.md)

---

## 🆘 Getting Help

- **GitHub Issues:** [project-ic-bot/issues](https://github.com/eeeeeric21/project-ic-bot/issues)
- **Telegram:** Message @AesculAI_helper_bot
- **Documentation:** This file and related docs

---

*Last updated: 2026-03-13*
