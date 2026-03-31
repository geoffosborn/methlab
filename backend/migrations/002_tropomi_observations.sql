-- TROPOMI CH4 wind-rotated observation results per facility

CREATE TABLE IF NOT EXISTS tropomi_observations (
    id                      SERIAL PRIMARY KEY,
    facility_id             INTEGER NOT NULL REFERENCES facilities(id),

    -- Time period
    period_start            DATE NOT NULL,
    period_end              DATE NOT NULL,
    aggregation_period      TEXT NOT NULL DEFAULT 'quarterly',  -- monthly, quarterly, annual

    -- CH4 enhancement metrics (ppb above background)
    mean_enhancement_ppb    DOUBLE PRECISION,
    max_enhancement_ppb     DOUBLE PRECISION,
    central_box_mean_ppb    DOUBLE PRECISION,

    -- Quality / coverage
    sample_count            INTEGER,           -- number of overpasses averaged
    valid_pixel_fraction    DOUBLE PRECISION,  -- fraction of grid with data

    -- Wind
    mean_wind_speed         DOUBLE PRECISION,  -- m/s

    -- Composite score
    intensity_score         DOUBLE PRECISION,  -- 0-100

    -- Background
    background_ch4_ppb      DOUBLE PRECISION,

    -- S3 artifact keys
    viz_s3_key              TEXT,               -- tear sheet PNG
    metrics_s3_key          TEXT,               -- metrics JSON
    field_s3_key            TEXT,               -- wind-rotated field numpy

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- One observation per facility per period
    UNIQUE (facility_id, period_start, period_end, aggregation_period)
);

CREATE INDEX IF NOT EXISTS idx_tropomi_facility ON tropomi_observations (facility_id);
CREATE INDEX IF NOT EXISTS idx_tropomi_period ON tropomi_observations (period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_tropomi_intensity ON tropomi_observations (intensity_score DESC);

CREATE TRIGGER tr_tropomi_observations_updated_at
    BEFORE UPDATE ON tropomi_observations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Processing jobs table for pipeline execution tracking
CREATE TABLE IF NOT EXISTS processing_jobs (
    id              SERIAL PRIMARY KEY,
    facility_id     INTEGER REFERENCES facilities(id),
    job_type        TEXT NOT NULL,       -- tropomi_screening, s2_detection, etc.
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_facility ON processing_jobs (facility_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs (status);
