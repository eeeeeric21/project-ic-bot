-- Medication Reminder System Schema
-- Run this in Supabase SQL Editor

-- ============================================
-- 1. MEDICATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS medications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id TEXT NOT NULL, -- telegram_id for simplicity
    
    -- Medication info
    name TEXT NOT NULL,           -- "Metformin"
    dosage TEXT,                   -- "500mg"
    instructions TEXT,             -- "Take with food"
    
    -- Schedule (stored as HH:MM strings for simplicity)
    reminder_times TEXT[] NOT NULL, -- {"08:00", "14:00", "20:00"}
    
    -- Tracking
    active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_by TEXT,              -- case worker telegram_id
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
    
    -- Reminder details
    scheduled_time TIMESTAMPTZ NOT NULL,
    reminder_sent BOOLEAN DEFAULT FALSE,
    reminder_sent_at TIMESTAMPTZ,
    
    -- Follow-up
    followup_sent BOOLEAN DEFAULT FALSE,
    followup_sent_at TIMESTAMPTZ,
    
    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'taken', 'skipped', 'missed')),
    responded_at TIMESTAMPTZ,
    skip_reason TEXT,
    
    -- Alert escalation
    case_worker_alerted BOOLEAN DEFAULT FALSE,
    case_worker_alerted_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 3. INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_reminders_patient ON medication_reminders(patient_id);
CREATE INDEX IF NOT EXISTS idx_reminders_scheduled ON medication_reminders(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON medication_reminders(status);

-- ============================================
-- 4. ROW LEVEL SECURITY
-- ============================================
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_reminders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anon access" ON medications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow anon access" ON medication_reminders FOR ALL USING (true) WITH CHECK (true);

-- ============================================
-- 5. SAMPLE DATA (for testing)
-- ============================================
-- Example: Eric takes Metformin twice daily
INSERT INTO medications (patient_id, name, dosage, instructions, reminder_times, created_by)
VALUES 
    ('706283824', 'Metformin', '500mg', 'Take with meals', ARRAY['08:00', '20:00'], '706283824'),
    ('8483200452', 'Lisinopril', '10mg', 'Take in the morning', ARRAY['09:00'], '706283824');
