-- Alerts table for threshold, detection, and compliance alerts

CREATE TABLE IF NOT EXISTS alerts (
    id                  SERIAL PRIMARY KEY,
    facility_id         INTEGER NOT NULL REFERENCES facilities(id),
    alert_type          TEXT NOT NULL,       -- threshold_exceedance, new_detection, nger_baseline_breach, trend_increase
    severity            TEXT NOT NULL,       -- critical, high, medium, low
    title               TEXT NOT NULL,
    description         TEXT,
    metadata            JSONB DEFAULT '{}',

    -- Acknowledgement
    acknowledged        BOOLEAN NOT NULL DEFAULT false,
    acknowledged_by     TEXT,
    acknowledged_at     TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alerts_facility ON alerts (facility_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts (acknowledged);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts (alert_type);
