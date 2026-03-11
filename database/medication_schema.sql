-- Medication Reminder System Schema
-- Run this in Supabase SQL Editor: https://xhonxrvogiamqhpfouoh.supabase.co/project/default/sql

-- ============================================
-- 1. MEDICATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS medications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id TEXT NOT NULL, -- telegram_id
    
    -- Medication info
    name TEXT NOT NULL,
    dosage TEXT,
    instructions TEXT,
    
    -- Schedule (HH:MM format)
    reminder_times TEXT[] NOT NULL,
    
    -- Tracking
    active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 2. MEDICATION REMINDERS TABLE (Tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS medication_reminders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    medication_id UUID REFERENCES medications(id) ON DELETE CASCADE,
    patient_id TEXT NOT NULL,
    medication_name TEXT NOT NULL,
    dosage TEXT,
    
    -- Reminder details
    scheduled_date DATE NOT NULL,
    scheduled_time TEXT NOT NULL,
    
    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'taken', 'skipped', 'missed')),
    
    -- Timestamps
    reminder_sent_at TIMESTAMPTZ,
    followup_sent_at TIMESTAMPTZ,
    responded_at TIMESTAMPTZ,
    case_worker_alerted_at TIMESTAMPTZ,
    
    -- Additional info
    skip_reason TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 3. INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_medications_active ON medications(active);
CREATE INDEX IF NOT EXISTS idx_reminders_patient ON medication_reminders(patient_id);
CREATE INDEX IF NOT EXISTS idx_reminders_date ON medication_reminders(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON medication_reminders(status);

-- ============================================
-- 4. ROW LEVEL SECURITY
-- ============================================
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_reminders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anon access" ON medications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow anon access" ON medication_reminders FOR ALL USING (true) WITH CHECK (true);

-- ============================================
-- 5. INITIAL DATA (Optional - can skip if adding via bot)
-- ============================================
-- Uncomment to add initial medications:
/*
INSERT INTO medications (patient_id, name, dosage, instructions, reminder_times, created_by)
VALUES 
    ('706283824', 'Metformin', '1000mg', 'Take with meals', ARRAY['08:00', '20:00'], '706283824'),
    ('706283824', 'Losartan', '50mg', 'For blood pressure', ARRAY['08:00'], '706283824'),
    ('706283824', 'Atorvastatin', '20mg', 'For cholesterol - take at bedtime', ARRAY['21:00'], '706283824'),
    ('8483200452', 'Metformin', '850mg', 'Take with breakfast and dinner', ARRAY['08:00', '19:00'], '706283824'),
    ('8483200452', 'Amlodipine', '5mg', 'Take once daily in the morning', ARRAY['08:00'], '706283824'),
    ('8483200452', 'Lisinopril', '10mg', 'Take once daily, can cause dizziness', ARRAY['08:00'], '706283824');
*/
