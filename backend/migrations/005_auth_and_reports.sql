-- Users and facility-level access control

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    full_name       TEXT,
    role            TEXT NOT NULL DEFAULT 'viewer',  -- admin, operator, viewer
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_facility_access (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    facility_id     INTEGER NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    access_level    TEXT NOT NULL DEFAULT 'read',  -- read, write, admin
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, facility_id)
);

CREATE INDEX IF NOT EXISTS idx_ufa_user ON user_facility_access (user_id);
CREATE INDEX IF NOT EXISTS idx_ufa_facility ON user_facility_access (facility_id);

CREATE TRIGGER tr_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- NGER compliance tracking
ALTER TABLE facilities
    ADD COLUMN IF NOT EXISTS nger_designated BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS safeguard_covered BOOLEAN DEFAULT false;

-- Report generation tracking
CREATE TABLE IF NOT EXISTS reports (
    id              SERIAL PRIMARY KEY,
    facility_id     INTEGER REFERENCES facilities(id),
    report_type     TEXT NOT NULL,       -- monthly_summary, compliance, detection_report
    period_start    DATE,
    period_end      DATE,
    format          TEXT NOT NULL DEFAULT 'pdf',  -- pdf, csv
    s3_key          TEXT,
    generated_by    INTEGER REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reports_facility ON reports (facility_id);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports (report_type);
