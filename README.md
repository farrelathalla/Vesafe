# VeSafe

> AI World Model + Agent Orchestration Network for Industrial Safety (K3) Intelligence

Built for the **Microsoft AI Impact Challenge** (Dicoding × Komdigi program). VeSafe automatically acquires public imagery of any pharmaceutical manufacturing facility, generates a navigable 3D Gaussian-splat world model, then deploys six specialized K3 (Kesehatan dan Keselamatan Kerja) agent teams into that model to identify and spatially annotate critical safety risks. Findings stream in real time and are exportable as PDF and FHIR R4 DiagnosticReport artifacts, all secured through InterSystems IRIS for Health.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment (Azure)](#production-deployment-azure)
- [Running Tests](#running-tests)
- [Six K3 Safety Domains](#six-k3-safety-domains)
- [Data Flow](#data-flow)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 0: InterSystems IRIS for Health                          │
│  (Secure Wallet · FHIR R4 · RBAC · Audit Log · IntegratedML)   │
├──────────────┬──────────────────────────┬───────────────────────┤
│  Layer 1     │  Layer 2                 │  Layer 3              │
│  Image       │  World Model Pipeline    │  Agent Orchestration  │
│  Acquisition │  Claude Vision →         │  6 K3 Domain Teams    │
│  ────────    │  Scene Graph →           │  Modal (A10G GPUs)    │
│  Street View │  World Labs API →        │  Azure Web PubSub     │
│  Places API  │  .spz binary             │  CSE (Azure OpenAI)   │
│  OSM         │  → Azure Blob Storage    │                       │
├──────────────┴──────────────────────────┴───────────────────────┤
│  Layer 4: Frontend                                              │
│  Next.js 15 · Azure Maps · React Three Fiber · Gaussian Splats │
│  Zustand · Azure Web PubSub · Azure Application Insights       │
└─────────────────────────────────────────────────────────────────┘
```

The system has four clearly separated concerns:

1. **IRIS for Health** — all persistent storage, encryption (Secure Wallet AES-256), FHIR R4 repository, RBAC, and audit logging. FastAPI calls IRIS via the `intersystems-irispython` SDK.
2. **Image Acquisition + World Model Pipeline** — `backend/pipeline/` pulls imagery from Google Street View / Places, classifies it with Claude Vision, builds a scene graph, submits to the World Labs Marble API to generate a Gaussian-splat world model, and stores the `.spz` asset in **Azure Blob Storage**.
3. **Agent Orchestration** — `backend/agents/` runs six K3 domain teams in parallel using `asyncio.gather`. Each team calls Anthropic Claude with Indonesian K3 standard prompts against the world model data. Raw results are merged by the Consensus Synthesis Engine (CSE), which uses **Azure OpenAI** for a final cross-domain pass. Findings are persisted to IRIS and published to **Azure Web PubSub** for real-time streaming.
4. **Frontend** — Next.js 15 App Router renders the facility map (**Azure Maps**), 3D world model viewer (React Three Fiber + `@mkkellogg/gaussian-splats-3d`), live findings panel (Azure Web PubSub), and PDF/FHIR export. **Azure Application Insights** provides telemetry.

---

## Tech Stack

### Backend (Python)

| Library | Version | Purpose |
|---|---|---|
| `fastapi` | 0.115.12 | HTTP and WebSocket API server |
| `uvicorn` | 0.34.0 | ASGI server |
| `pydantic` / `pydantic-settings` | 2.11.3 / 2.8.1 | Data validation and settings management |
| `httpx` | 0.28.1 | Async HTTP client |
| `openai` | latest | Azure OpenAI SDK (CSE synthesis) |
| `azure-storage-blob` | latest | Azure Blob Storage for 3D assets |
| `azure-messaging-webpubsubservice` | latest | Azure Web PubSub for real-time streaming |
| `reportlab` | 4.3.1 | PDF report generation |
| `pytest` | 8.3.5 | Test runner |
| `intersystems-irispython` | latest | IRIS for Health SDK |
| `anthropic` | latest | Claude Vision API for classification and agent teams |
| `modal` | latest | Serverless GPU (A10G) hosting for agent inference |

### Frontend (TypeScript)

| Library | Version | Purpose |
|---|---|---|
| `next` | 15.5.14 | React framework, App Router |
| `react` | 19.0.0 | UI rendering |
| `@react-three/fiber` | 9.1.0 | 3D world model viewer |
| `@react-three/drei` | 10.0.4 | Three.js helpers |
| `@mkkellogg/gaussian-splats-3d` | 0.4.7 | Gaussian splat renderer |
| `three` | 0.174.0 | Underlying 3D engine |
| `azure-maps-control` | v3 | Facility selection map |
| `@microsoft/applicationinsights-web` | latest | Azure Application Insights telemetry |
| `zustand` | 5.0.3 | Global viewer and interaction state |
| `recharts` | 2.15.1 | Risk score and coverage charts |
| `react-dropzone` | 14.3.8 | Supplemental image upload |
| `tus-js-client` | 4.2.3 | Resumable uploads |

### External Services

| Service | Purpose |
|---|---|
| **InterSystems IRIS for Health** | Primary datastore, FHIR R4, encryption, RBAC |
| **Azure OpenAI Service** | Consensus Synthesis Engine (CSE) — cross-domain finding synthesis |
| **Azure Blob Storage** | `.spz` world model asset storage |
| **Azure Maps** | Facility map tiles and geocoding |
| **Azure Web PubSub** | Real-time WebSocket for scan findings |
| **Azure App Service** | FastAPI backend hosting |
| **Azure Static Web Apps** | Next.js frontend hosting |
| **Azure Application Insights** | Telemetry and performance monitoring |
| **Google Street View / Places API** | Public imagery acquisition |
| **World Labs Marble API** | Gaussian-splat 3D world model generation |
| **Anthropic Claude** | Vision classification, six K3 agent domain teams |
| **Modal** | Serverless A10G GPU hosting for agent inference |

---

## Repository Layout

```
vesafe/
├── backend/
│   ├── api/           # FastAPI route modules
│   ├── agents/        # Six K3 domain agent teams + consensus synthesis
│   │   ├── ica_team.py        # Pencegahan Kontaminasi
│   │   ├── msa_team.py        # Penanganan B3
│   │   ├── fra_team.py        # Keselamatan Alat Berat
│   │   ├── era_team.py        # Tanggap Darurat
│   │   ├── pfa_team.py        # Alur Produksi
│   │   ├── sca_team.py        # Komunikasi K3
│   │   ├── consensus.py       # CSE — Azure OpenAI cross-domain synthesis
│   │   └── orchestrator.py
│   ├── db/            # Persistence adapters (iris_client, redis_client, azure_blob_client)
│   ├── pipeline/      # Image acquisition → classify → scene graph → world model
│   ├── reports/       # PDF and FHIR DiagnosticReport export
│   ├── config.py      # Pydantic Settings (reads .env)
│   ├── models.py      # Shared Pydantic data models
│   └── main.py        # FastAPI app factory
├── frontend/
│   ├── app/           # Next.js App Router pages
│   ├── components/    # UI components
│   ├── hooks/         # WebSocket, model-loading hooks
│   ├── store/         # Zustand global state
│   └── lib/           # API client, Azure Maps, Application Insights
├── iris/              # IRIS deployment config
├── docs/              # Architecture, design docs, product specs
├── scripts/
└── tests/             # Backend pytest suite
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Docker + Docker Compose** (required for IRIS)
- **Azure account** with the following services provisioned (see [SETUP.md](SETUP.md)):
  - Azure OpenAI Service (gpt-4o-mini deployment)
  - Azure Blob Storage
  - Azure Maps
  - Azure Web PubSub
  - Azure Application Insights
- API keys for: Google Maps Platform, World Labs, Anthropic (see [SETUP.md](SETUP.md))

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all values before starting.

```bash
cp .env.example .env
```

> **Synthetic fallbacks**: `MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true` skips all external API calls and returns deterministic K3 findings. Use this for local development and repeatable demos after initial real scan.

---

## Local Development

### 1. Start infrastructure (IRIS)

```bash
docker compose up iris -d
```

Wait ~30 seconds for IRIS to initialize.

### 2. Set up the Python backend

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Fill in API keys, or set MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true for demo mode
```

### 4. Start the backend

```bash
./scripts/start-backend.sh
# FastAPI at http://127.0.0.1:8000
# Docs at http://127.0.0.1:8000/docs
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
# Next.js at http://localhost:3000
```

---

## Docker Deployment

```bash
docker compose up --build
docker compose logs -f backend
docker compose down
```

> **Security:** IRIS ports `1972` and `52773` are on the `internal` network only.

---

## Production Deployment (Azure)

### Backend — Azure App Service

```bash
# Build Docker image
docker build -t vesafe-backend ./backend

# Push to Azure Container Registry
az acr login --name <your-acr>
docker tag vesafe-backend <your-acr>.azurecr.io/vesafe-backend:latest
docker push <your-acr>.azurecr.io/vesafe-backend:latest

# Deploy to App Service
az webapp create --resource-group vesafe-rg --plan vesafe-plan \
  --name vesafe-api --deployment-container-image-name \
  <your-acr>.azurecr.io/vesafe-backend:latest
```

### Frontend — Azure Static Web Apps

```bash
cd frontend
npm run build
# Deploy via GitHub Actions (auto-configured by Azure Static Web Apps)
# or: npx @azure/static-web-apps-cli deploy .next --env production
```

---

## Running Tests

```bash
source .venv/bin/activate
pytest
pytest tests/backend/test_consensus.py -v
pytest --cov=backend
```

Tests use in-memory IRIS/Azure stubs and do not require external API keys.

---

## Six K3 Safety Domains

Each agent team ingests the facility's world model data and produces spatially anchored `Finding` records ranked by severity.

| Team | Module | Domain | Indonesian Standard |
|---|---|---|---|
| **ICA** | `agents/ica_team.py` | Pencegahan Kontaminasi | CPOB BPOM RI |
| **MSA** | `agents/msa_team.py` | Penanganan B3 | PP No. 74/2001, Permenaker 187/MEN/1999 |
| **FRA** | `agents/fra_team.py` | Keselamatan Alat Berat | SMK3 PP No. 50/2012, SNI |
| **ERA** | `agents/era_team.py` | Tanggap Darurat | Permenaker No. 04/MEN/1980 |
| **PFA** | `agents/pfa_team.py` | Alur Produksi | CPOB Bab 3 — Bangunan dan Fasilitas |
| **SCA** | `agents/sca_team.py` | Komunikasi K3 | SMK3 + ISO 45001:2018 |

All six run concurrently via `asyncio.gather` in `agents/orchestrator.py`. The **Consensus Synthesis Engine** (`agents/consensus.py`) deduplicates overlapping findings and re-ranks the final list using **Azure OpenAI**.

---

## Data Flow

```
User selects facility on Azure Maps
    ↓
POST /api/facilities  →  Google Geocoding + Places lookup
    ↓
pipeline/image_acquisition.py  →  Street View + Places Photos
    ↓
pipeline/classify.py  →  Claude Vision: tag area types, K3 hazard signals
    ↓
pipeline/scene_graph.py  →  structured scene graph JSON
    ↓
pipeline/world_model.py  →  World Labs Marble API  →  .spz → Azure Blob Storage
    ↓
POST /api/scans  →  agents/orchestrator.py
    ↓
asyncio.gather(ica, msa, fra, era, pfa, sca)  [Modal A10G GPUs]
    ↓
agents/consensus.py  →  CSE synthesis (Azure OpenAI cross-domain pass)
    ↓
iris_client.write_findings()  →  IRIS Secure Wallet storage
    ↓
azure_pubsub_client.publish()  →  Azure Web PubSub → browser live findings panel
    ↓
/api/reports  →  PDF (ReportLab) or FHIR DiagnosticReport (IRIS FHIR R4)
```
