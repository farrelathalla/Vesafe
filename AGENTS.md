# AGENTS.md

This repository follows an agent-first workflow. Read this file before touching any code.

## Mission

Build VeSafe: a Next.js 15 + FastAPI platform that acquires public imagery of pharmaceutical manufacturing facilities, generates a navigable Gaussian-splat 3D world model via World Labs, deploys six K3 (Kesehatan dan Keselamatan Kerja) agent teams (Anthropic Claude), and exports findings as PDF and FHIR R4 artifacts — secured through InterSystems IRIS for Health, with Azure OpenAI powering the Consensus Synthesis Engine.

Built for the **Microsoft AI Impact Challenge** (Dicoding × Komdigi).

## Working Rules

- Read the relevant spec and docs before editing.
- Keep the repository as the system of record. If a decision matters, encode it in `docs/`.
- Prefer small, legible changes over hidden cleverness.
- Maintain the PRD contract in `PRD.md` unless a task explicitly changes product scope.
- Preserve the directory layout promised in the PRD.
- When implementation diverges from production integrations, keep interfaces stable and note the development fallback in docs.
- Add or update tests when behavior changes.
- Favor deterministic mockable seams for external services: Google APIs, Anthropic, World Labs, IRIS, Azure services, Modal.
- Never store secrets in code — all credentials come from `backend/config.py` via `pydantic-settings` and `.env`.
- IRIS ports `1972` and `52773` are internal-only. Never expose them publicly.

## Entry Points

- Product and scope: [`PRD.md`](PRD.md)
- Setup guide: [`SETUP.md`](SETUP.md)
- Architecture map: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Frontend guidance: [`docs/FRONTEND.md`](docs/FRONTEND.md)
- Reliability expectations: [`docs/RELIABILITY.md`](docs/RELIABILITY.md)
- Security expectations: [`docs/SECURITY.md`](docs/SECURITY.md)

## Repository Map

```
backend/api/          HTTP + WebSocket transport only — no business logic here
backend/agents/       Six K3 domain teams, consensus synthesis, orchestrator
backend/db/           Persistence adapters — iris_client, redis_client, azure_blob_client
backend/pipeline/     Image acquisition → classify → scene graph → world model
backend/reports/      PDF (ReportLab) and FHIR DiagnosticReport generation
backend/config.py     Pydantic Settings — all env vars loaded here
backend/models.py     Shared Pydantic data models (Finding, Scan, Facility, etc.)
frontend/app/         Next.js App Router pages
frontend/components/  UI components: viewer/, findings/, facility/, shared/
frontend/hooks/       WebSocket, model-loading, coverage hooks
frontend/store/       Zustand global state
frontend/lib/         API client, Azure Maps init, Application Insights
iris/                 IRIS CPF config, FHIR config JSON, first-run init.sh
docs/                 Source of truth for architecture, plans, quality, security
tests/                Backend pytest suite (uses in-memory stubs, no live API keys)
```

## Development Setup

```bash
# 1. Infrastructure (IRIS only — Azure Web PubSub replaces Redis)
docker compose up iris -d

# 2. Python backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env   # fill in keys, or set MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true

# 3. Start backend (uvicorn, port 8000, hot-reload)
./scripts/start-backend.sh

# 4. Frontend
cd frontend && npm install && npm run dev   # port 3000

# 5. Tests
pytest
```

`MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true` bypasses all live external API calls and returns deterministic K3 pharma-factory findings — use for local development without API keys.

## Agent Architecture

Six K3 domain teams run concurrently in `agents/orchestrator.py` via `asyncio.gather`. Each team module exposes a single `async def run(scan_id, world_model_dict) -> list[dict]` function.

| Team | File | K3 Domain | Indonesian Standard |
|---|---|---|---|
| ICA | `agents/ica_team.py` | Pencegahan Kontaminasi | CPOB BPOM RI |
| MSA | `agents/msa_team.py` | Penanganan B3 | PP 74/2001, Permenaker 187/1999 |
| FRA | `agents/fra_team.py` | Keselamatan Alat Berat | SMK3 PP 50/2012, SNI |
| ERA | `agents/era_team.py` | Tanggap Darurat | Permenaker 04/MEN/1980 |
| PFA | `agents/pfa_team.py` | Alur Produksi | CPOB Bab 3 |
| SCA | `agents/sca_team.py` | Komunikasi K3 | SMK3 + ISO 45001:2018 |

After gather, `agents/consensus.py` runs the Consensus Synthesis Engine (CSE) — an **Azure OpenAI** pass that deduplicates and re-ranks findings.

## Persistence Layer

All reads and writes go through adapters in `backend/db/`:

- `iris_client.py` — IRIS for Health via `intersystems-irispython`.
- `redis_client.py` — Redis pub/sub (fallback) or Azure Web PubSub wrapper.
- `azure_blob_client.py` — Azure Blob Storage for `.spz` world model assets.

## Azure Integration Points

| Service | Adapter | Config Key |
|---|---|---|
| Azure OpenAI | `agents/providers/azure_openai_provider.py` | `AZURE_OPENAI_*` |
| Azure Blob Storage | `db/azure_blob_client.py` | `AZURE_STORAGE_*` |
| Azure Maps | `frontend/lib/azureMaps.ts` | `NEXT_PUBLIC_AZURE_MAPS_KEY` |
| Azure Web PubSub | `db/redis_client.py` (adapter) | `AZURE_WEB_PUBSUB_*` |
| Azure App Insights | `frontend/lib/insights.ts` | `NEXT_PUBLIC_AZURE_APP_INSIGHTS_*` |
