-- MethLab: Facilities table
-- Requires PostGIS extension

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS facilities (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    facility_type   TEXT NOT NULL DEFAULT 'coal_mine',
    state           TEXT,                               -- QLD, NSW, VIC, etc.
    operator        TEXT,
    commodity       TEXT,                               -- coal, gas, etc.

    -- Location
    centroid        geography(Point, 4326) NOT NULL,
    boundary        geography(Polygon, 4326),

    -- Regulatory
    nger_id         TEXT,                               -- NGER facility ID
    nger_baseline   DOUBLE PRECISION,                   -- baseline emissions (t CO2-e/yr)

    -- Status
    status          TEXT NOT NULL DEFAULT 'active',     -- active, closed, care_and_maintenance

    -- Flexible metadata (source URLs, alternate names, etc.)
    metadata        JSONB DEFAULT '{}',

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Spatial index on centroid for bbox queries
CREATE INDEX IF NOT EXISTS idx_facilities_centroid ON facilities USING GIST (centroid);

-- Index for common filters
CREATE INDEX IF NOT EXISTS idx_facilities_type ON facilities (facility_type);
CREATE INDEX IF NOT EXISTS idx_facilities_state ON facilities (state);
CREATE INDEX IF NOT EXISTS idx_facilities_status ON facilities (status);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_facilities_updated_at
    BEFORE UPDATE ON facilities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
