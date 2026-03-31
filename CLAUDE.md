# MethLab Monorepo

Methane monitoring platform for Australian coal mining operations.

## Structure

```
frontend/   — Next.js 16, React 19, Tailwind v4, three.js (port 3100)
backend/    — Python/FastAPI, uv workspace (port 8020 API, 8023 ML)
infra/      — Caddyfile, systemd units, deploy script
docs/       — Strategy docs, assessments, screenshots
```

## Quick Start

```bash
make install    # Install all dependencies
make dev        # Run frontend + backend concurrently
make up         # Docker Compose (db + api + frontend)
```

## Backend Apps (uv workspace)

- `apps/api` — Core REST API (facilities, tropomi, sentinel2, alerts, auth, reports)
- `apps/ml` — GPU inference (plume segmentation/classification, PyTorch)
- `apps/tropomi` — TROPOMI CH4 screening pipeline
- `apps/sentinel2` — Sentinel-2 SWIR plume quantification
- `apps/registry` — Facility seed data (coal mines)
- `packages/common` — Shared pydantic utilities

## Environment Variables

- Frontend: `METHLAB_API_BASE` (default: `http://localhost:8020`)
- Backend: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `AWS_REGION`, `S3_BUCKET`

## Deployment

Single server at `methlab.geosynergy.com.au` (frontend) and `methlab-api.geosynergy.com.au` (API).

```bash
make deploy     # or: bash infra/deploy.sh
```
