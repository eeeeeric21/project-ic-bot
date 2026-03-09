-- Project IC Database Schema
-- Run this in Supabase SQL Editor: https://xhonxrvogiamqhpfouoh.supabase.co/project/default/sql

-- ============================================
-- 1. PATIENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS patients (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    preferred_name TEXT,
    age INTEGER,
    phone TEXT,
    telegram_id TEXT,
    
    -- Health info
    conditions TEXT[], -- array of conditions
    medications JSONB DEFAULT '[]'::jsonb, -- [{name, dosage, frequency}]
    allergies TEXT[],
    
    -- Personal context for conversations
    interests TEXT[],
    family_members JSONB DEFAULT '[]'::jsonb, -- [{name, relationship}]
    language_preference TEXT DEFAULT 'en', -- 'en', 'zh', 'ms', 'ta'
    
    -- Alert settings
    case_worker_id TEXT, -- telegram chat id for alerts
    emergency_contact JSONB, -- {name, phone, relationship}
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================
-- 2. CHECKINS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS checkins (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Session info
    session_type TEXT CHECK (session_type IN ('morning', 'evening', 'ad-hoc')),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    
    -- Analysis results
    detected_categories TEXT[], -- ['pain', 'distress', 'cognitive']
    risk_score INTEGER DEFAULT 0,
    risk_level TEXT CHECK (risk_level IN ('GREEN', 'YELLOW', 'ORANGE', 'RED')),
    
    -- Audio analysis (if voice check-in)
    audio_url TEXT,
    emotion_detected TEXT,
    paralinguistics JSONB,
    
    -- Summary
    summary TEXT,
    follow_up_needed BOOLEAN DEFAULT FALSE
);

-- ============================================
-- 3. MESSAGES TABLE (Conversation History)
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    checkin_id UUID REFERENCES checkins(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    
    role TEXT CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    -- Analysis of this message
    detected_signals JSONB, -- {categories: [], keywords: []}
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 4. ALERTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    checkin_id UUID REFERENCES checkins(id) ON DELETE SET NULL,
    
    -- Alert details
    alert_level TEXT CHECK (alert_level IN ('YELLOW', 'ORANGE', 'RED')),
    title TEXT NOT NULL,
    message TEXT,
    detected_issues TEXT[],
    
    -- Delivery status
    telegram_sent BOOLEAN DEFAULT FALSE,
    telegram_sent_at TIMESTAMPTZ,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMPTZ,
    sms_sent BOOLEAN DEFAULT FALSE,
    
    -- Response tracking
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT, -- who acknowledged (case worker name/id)
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 5. INDEXES for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_checkins_patient_id ON checkins(patient_id);
CREATE INDEX IF NOT EXISTS idx_checkins_started_at ON checkins(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_checkin_id ON messages(checkin_id);
CREATE INDEX IF NOT EXISTS idx_alerts_patient_id ON alerts(patient_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);

-- ============================================
-- 6. ROW LEVEL SECURITY (Optional but recommended)
-- ============================================
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkins ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Allow anon key to read/write (adjust for production security)
CREATE POLICY "Allow anon access" ON patients FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow anon access" ON checkins FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow anon access" ON messages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow anon access" ON alerts FOR ALL USING (true) WITH CHECK (true);

-- ============================================
-- 7. SAMPLE DATA (for testing)
-- ============================================
INSERT INTO patients (name, preferred_name, age, conditions, interests, language_preference, case_worker_id)
VALUES 
    ('Tan Ah Kow', 'Uncle Tan', 72, 
     ARRAY['diabetes', 'hypertension', 'knee arthritis'],
     ARRAY['gardening', 'mahjong', 'grandchildren'],
     'en',
     '706283824'
    ),
    ('Lee Mei Ling', 'Auntie Mei', 68,
     ARRAY['high cholesterol'],
     ARRAY['cooking', 'TV dramas', 'morning walks'],
     'en',
     '706283824'
    );
