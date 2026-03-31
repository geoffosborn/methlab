-- Sentinel-2 individual plume detections with emission quantification

CREATE TABLE IF NOT EXISTS s2_detections (
    id                      SERIAL PRIMARY KEY,
    facility_id             INTEGER NOT NULL REFERENCES facilities(id),
    scene_id                TEXT NOT NULL,
    scene_datetime          TIMESTAMPTZ NOT NULL,

    -- Emission quantification (Varon IME method)
    emission_rate_kg_hr     DOUBLE PRECISION,   -- Q = IME × Ueff / L
    uncertainty_kg_hr       DOUBLE PRECISION,   -- 1σ uncertainty
    ime_kg                  DOUBLE PRECISION,   -- Integrated Mass Enhancement
    effective_wind_m_s      DOUBLE PRECISION,   -- Ueff = 0.33×U10 + 0.45
    plume_length_m          DOUBLE PRECISION,   -- L effective plume length

    -- Plume properties
    plume_area_m2           DOUBLE PRECISION,
    plume_pixels            INTEGER,
    mean_enhancement        DOUBLE PRECISION,   -- Mean ΔB12/B12 in plume
    max_enhancement         DOUBLE PRECISION,

    -- Meteorology
    wind_speed_10m          DOUBLE PRECISION,   -- ERA5 10m wind (m/s)
    wind_direction          DOUBLE PRECISION,   -- Meteorological direction FROM

    -- Viewing geometry
    solar_zenith            DOUBLE PRECISION,
    view_zenith             DOUBLE PRECISION,
    cloud_cover             DOUBLE PRECISION,

    -- Quality
    confidence              TEXT DEFAULT 'medium',   -- high, medium, low

    -- S3 artifact keys
    enhancement_s3_key      TEXT,
    plume_mask_s3_key       TEXT,
    viz_s3_key              TEXT,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_s2_facility ON s2_detections (facility_id);
CREATE INDEX IF NOT EXISTS idx_s2_datetime ON s2_detections (scene_datetime DESC);
CREATE INDEX IF NOT EXISTS idx_s2_emission ON s2_detections (emission_rate_kg_hr DESC);
CREATE INDEX IF NOT EXISTS idx_s2_confidence ON s2_detections (confidence);
