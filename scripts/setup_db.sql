-- ============================================================
-- Averlyn Vaccine Tracker — Supabase Database Setup
-- Run this in the Supabase SQL Editor to create all tables,
-- RLS policies, triggers, and seed data.
-- ============================================================

-- 1. Create tables
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS baby (
    id          integer PRIMARY KEY DEFAULT 1,
    name        text NOT NULL,
    birth_date  date NOT NULL
);

CREATE TABLE IF NOT EXISTS vaccines (
    id              text PRIMARY KEY,
    name            text NOT NULL,
    name_en         text NOT NULL,
    subtitle        text,
    type            text NOT NULL CHECK (type IN ('public', 'self-paid')),
    done            boolean NOT NULL DEFAULT false,
    done_date       date,
    scheduled_date  date,
    price           integer,
    description     text NOT NULL,
    side_effects    text,
    notes           text,
    display_order   integer NOT NULL,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS allowed_emails (
    email text PRIMARY KEY
);

-- 2. Seed allowed emails
-- ------------------------------------------------------------

INSERT INTO allowed_emails (email) VALUES
    ('feverjp751111@gmail.com'),
    ('aaa2003.loveyou@gmail.com')
ON CONFLICT (email) DO NOTHING;

-- 3. Seed baby record
-- ------------------------------------------------------------

INSERT INTO baby (id, name, birth_date) VALUES
    (1, 'Averlyn', '2025-12-03')
ON CONFLICT (id) DO NOTHING;

-- 4. Auto-update updated_at trigger
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON vaccines;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON vaccines
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- 5. RLS helper function
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_allowed_user()
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM allowed_emails
        WHERE email = auth.jwt() ->> 'email'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 6. Enable RLS and create policies
-- ------------------------------------------------------------

-- vaccines
ALTER TABLE vaccines ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allowed users read vaccines" ON vaccines;
CREATE POLICY "Allowed users read vaccines" ON vaccines
    FOR SELECT USING (is_allowed_user());

DROP POLICY IF EXISTS "Allowed users update vaccines" ON vaccines;
CREATE POLICY "Allowed users update vaccines" ON vaccines
    FOR UPDATE USING (is_allowed_user())
    WITH CHECK (is_allowed_user());

-- baby
ALTER TABLE baby ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allowed users read baby" ON baby;
CREATE POLICY "Allowed users read baby" ON baby
    FOR SELECT USING (is_allowed_user());

-- allowed_emails
ALTER TABLE allowed_emails ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allowed users read allowed_emails" ON allowed_emails;
CREATE POLICY "Allowed users read allowed_emails" ON allowed_emails
    FOR SELECT USING (is_allowed_user());
