# VeSafe

> **Spatial Command Center** untuk Pengawasan K3 dan Kepatuhan Regulasi Fasilitas Farmasi secara Otonom

Dibangun untuk **Microsoft Elevate Training Center (METC) Hackathon** — Topik: Pharma/Health.

VeSafe adalah platform yang mengintegrasikan CCTV dan sensor IoT ke dalam model **3D Gaussian Splat Digital Twin** untuk pengawasan fasilitas farmasi yang otonom dan patuh terhadap regulasi BPOM CPOB 2024/2025. Platform ini mengeliminasi ketergantungan pada inspeksi manual dengan **Agentic AI** yang memantau area terbatas 24/7 — mendeteksi pelanggaran APD (masker/hairnet), pintu area steril yang terbuka melebihi toleransi, hingga deviasi parameter lingkungan (suhu, partikel) secara instan.

**Tim:**
- **Farrel Athalla Putra** — Arsitektur YOLO, integrasi Azure Web PubSub, optimasi backend pada Modal (A10G GPUs)
- **Josephine Larissa Rachmadiana** — Penyelarasan fitur dengan regulasi farmasi (CPOB/WHO), implementasi FHIR R4, analisis risiko operasional

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solusi: Fitur Utama](#solusi-fitur-utama)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment (Azure)](#production-deployment-azure)
- [Running Tests](#running-tests)
- [Cara Penggunaan](#cara-penggunaan)
- [Data Flow](#data-flow)
- [Analisis Komparatif](#analisis-komparatif)
- [Roadmap](#roadmap)

---

## Problem Statement

Monitoring K3 dan kualitas di manufaktur farmasi saat ini terjebak dalam ketergantungan pada **pengawasan manual**, menyebabkan waktu deteksi laten yang tinggi. Berdasarkan standar **BPOM CPOB 2024/2025**, fasilitas sterilisasi (Grade A/B) mewajibkan pemantauan parameter lingkungan tanpa henti — namun praktik di lapangan masih sangat manual dan tidak memiliki sistem peringatan dini yang proaktif.

**Risiko nyata:**
- Deviasi suhu pukul 02:00 baru diketahui pukul 08:00 → denaturasi protein pada batch → kerugian IDR 500 juta hingga miliaran Rupiah per insiden *(WHO Technical Report Series, No. 961)*
- Pintu airlock terbuka >30 detik → kontaminasi silang yang tidak terdeteksi
- Staf QC harus mendokumentasikan posisi sensor secara manual (foto satu per satu) untuk prinsip ALCOA+

---

## Solusi: Fitur Utama

### 3D Gaussian Splat Digital Twin
Membangun replika digital fasilitas menggunakan **World Labs Marble API** untuk memvalidasi kesesuaian tata letak lab terhadap regulasi industri secara otomatis. Admin memetakan ID sensor dan kamera ke posisi aslinya di model 3D, menggantikan proses dokumentasi foto manual.

### Real-Time Agentic AI (Object Detection)
Implementasi model **YOLO** pada **Modal (A10G GPUs)** untuk mendeteksi ketidakpatuhan APD (masker/hairnet) secara instan — deteksi dalam **<5 detik** tanpa menunggu inspeksi manual. Jika ada pekerja tidak menggunakan masker atau pintu akses terbuka terlalu lama, sistem langsung memicu alert visual di peta 3D.

### Spatial IoT Alert System
Mengintegrasikan sensor lingkungan ke koordinat 3D via **InterSystems IRIS** untuk memberikan peringatan visual instan saat parameter suhu atau partikel keluar dari batas aman. Data IoT terikat permanen pada koordinat spasial 3D (Spatial Anchoring), menjamin kepatuhan mutlak terhadap prinsip **ALCOA+**.

### Automated Audit Reporting (FHIR R4)
Mengotomatisasi dokumentasi ALCOA+ — ekspor laporan standar **FHIR R4** on-demand untuk pembuktian kepatuhan operasional kepada BPOM secara instan. Menggantikan proses konsolidasi data manual yang memakan waktu 3–5 hari.

### Consensus Synthesis Engine (CSE)
Menggunakan **Azure OpenAI** untuk menganalisis data lintas domain (visual dan sensorik) guna memberikan laporan risiko yang akurat dan terkonsolidasi.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 0: InterSystems IRIS for Health                          │
│  (Secure Wallet · FHIR R4 · RBAC · Audit Log · IntegratedML)   │
├──────────────┬──────────────────────────┬───────────────────────┤
│  Layer 1     │  Layer 2                 │  Layer 3              │
│  CCTV +      │  World Model Pipeline    │  Agentic AI           │
│  Sensor IoT  │  World Labs Marble API → │  YOLO (APD detect)    │
│  Upload      │  Gaussian Splat 3D Twin  │  Modal (A10G GPUs)    │
│  ────────    │  → Azure Blob Storage    │  Azure Web PubSub     │
│  Drag & Drop │                          │  CSE (Azure OpenAI)   │
├──────────────┴──────────────────────────┴───────────────────────┤
│  Layer 4: Frontend (Spatial Command Center)                     │
│  Next.js 15 · React Three Fiber · Gaussian Splats              │
│  Zustand · Azure Web PubSub · Azure Application Insights       │
└─────────────────────────────────────────────────────────────────┘
```

Empat concern yang terpisah jelas:

1. **IRIS for Health** — semua persistent storage, enkripsi (Secure Wallet AES-256), FHIR R4 repository, RBAC, dan audit logging. FastAPI memanggil IRIS via SDK `intersystems-irispython`.
2. **World Model Pipeline** — `backend/pipeline/` menerima video/foto fasilitas, mengklasifikasikannya dengan Claude Vision, membangun scene graph, dan mensubmit ke World Labs Marble API untuk menghasilkan Gaussian-splat 3D, lalu menyimpan `.spz` di **Azure Blob Storage**.
3. **Agentic AI Monitoring** — `backend/agents/` menjalankan deteksi YOLO secara real-time untuk APD compliance dan pemantauan parameter IoT. Consensus Synthesis Engine (CSE) menggunakan **Azure OpenAI** untuk laporan risiko lintas domain. Temuan dipersistensikan ke IRIS dan dipublikasikan ke **Azure Web PubSub** untuk streaming real-time.
4. **Frontend (Spatial Command Center)** — Next.js 15 App Router merender dashboard facility, 3D world model viewer (React Three Fiber + `@mkkellogg/gaussian-splats-3d`), live alert panel (Azure Web PubSub), dan ekspor PDF/FHIR. **Azure Application Insights** menyediakan telemetri.

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
| `anthropic` | latest | Claude Vision API for classification |
| `modal` | latest | Serverless GPU (A10G) hosting for YOLO inference |

### Frontend (TypeScript)

| Library | Version | Purpose |
|---|---|---|
| `next` | 15.5.14 | React framework, App Router |
| `react` | 19.0.0 | UI rendering |
| `@react-three/fiber` | 9.1.0 | 3D world model viewer |
| `@react-three/drei` | 10.0.4 | Three.js helpers |
| `@mkkellogg/gaussian-splats-3d` | 0.4.7 | Gaussian splat renderer |
| `three` | 0.174.0 | Underlying 3D engine |
| `@microsoft/applicationinsights-web` | latest | Azure Application Insights telemetry |
| `zustand` | 5.0.3 | Global viewer and interaction state |
| `recharts` | 2.15.1 | Risk score and coverage charts |
| `react-dropzone` | 14.3.8 | Supplemental image upload |
| `tus-js-client` | 4.2.3 | Resumable uploads |

### External Services

| Service | Purpose |
|---|---|
| **InterSystems IRIS for Health** | Primary datastore, FHIR R4, enkripsi, RBAC, Spatial IoT anchor |
| **Azure OpenAI Service** | Consensus Synthesis Engine (CSE) — cross-domain risk synthesis |
| **Azure Blob Storage** | `.spz` world model asset storage |
| **Azure Web PubSub** | Real-time WebSocket untuk live alert dan incident stream |
| **Azure App Service** | FastAPI backend hosting |
| **Azure Static Web Apps** | Next.js frontend hosting |
| **Azure Application Insights** | Telemetri dan performance monitoring |
| **World Labs Marble API** | Gaussian-splat 3D world model generation |
| **Anthropic Claude** | Vision classification dan scene graph |
| **Modal** | Serverless A10G GPU hosting untuk YOLO inference real-time |

---

## Repository Layout

```
vesafe/
├── backend/
│   ├── api/           # FastAPI route modules
│   ├── agents/        # Agentic AI + consensus synthesis
│   │   ├── ica_team.py        # Pencegahan Kontaminasi
│   │   ├── msa_team.py        # Penanganan B3
│   │   ├── fra_team.py        # Keselamatan Alat Berat
│   │   ├── era_team.py        # Tanggap Darurat
│   │   ├── pfa_team.py        # Alur Produksi
│   │   ├── sca_team.py        # Komunikasi K3
│   │   ├── consensus.py       # CSE — Azure OpenAI cross-domain synthesis
│   │   └── orchestrator.py
│   ├── db/            # Persistence adapters (iris_client, azure_blob_client)
│   ├── pipeline/      # Video/image → classify → scene graph → world model
│   ├── reports/       # PDF dan FHIR R4 DiagnosticReport export
│   ├── config.py      # Pydantic Settings (reads .env)
│   ├── models.py      # Shared Pydantic data models
│   └── main.py        # FastAPI app factory
├── frontend/
│   ├── app/           # Next.js App Router pages (Spatial Command Center)
│   ├── components/    # UI components (3D viewer, alert panel, dashboard)
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
- **Azure account** dengan services berikut (lihat [SETUP.md](SETUP.md)):
  - Azure OpenAI Service (gpt-4o-mini deployment)
  - Azure Blob Storage
  - Azure Web PubSub
  - Azure Application Insights
- API keys untuk: World Labs, Anthropic (lihat [SETUP.md](SETUP.md))

---

## Environment Variables

Copy `.env.example` ke `.env` dan isi semua nilai sebelum memulai.

```bash
cp .env.example .env
```

> **Synthetic fallbacks**: `MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true` melewati semua external API call dan mengembalikan K3 findings yang deterministik. Gunakan untuk local development dan repeatable demo.

---

## Local Development

### 1. Start infrastructure (IRIS)

```bash
docker compose up iris -d
```

Tunggu ~30 detik agar IRIS terinisialisasi.

### 2. Set up Python backend

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Isi API keys, atau set MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true untuk demo mode
```

### 4. Start backend

```bash
./scripts/start-backend.sh
# FastAPI at http://127.0.0.1:8000
# Docs at http://127.0.0.1:8000/docs
```

### 5. Start frontend

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

> **Security:** IRIS ports `1972` dan `52773` hanya ada di network `internal`.

---

## Production Deployment (Azure)

### Backend — Azure App Service

```bash
docker build -t vesafe-backend ./backend
az acr login --name <your-acr>
docker tag vesafe-backend <your-acr>.azurecr.io/vesafe-backend:latest
docker push <your-acr>.azurecr.io/vesafe-backend:latest
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

Tests menggunakan in-memory IRIS/Azure stubs dan tidak memerlukan external API keys.

---

## Cara Penggunaan

1. **Digital Site Audit** — User mengunggah video internal lab; sistem membangun model 3D Gaussian Splat dan melakukan pengecekan otomatis terhadap standar penempatan ruang sesuai regulasi.
2. **Virtual Sensor Tagging** — Admin memetakan ID sensor dan kamera ke posisi aslinya di model 3D, menggantikan proses dokumentasi foto manual (memenuhi prinsip ALCOA+).
3. **Active Monitoring** — AI memantau live feed secara background 24/7. Jika ada pekerja tidak menggunakan masker/hairnet atau pintu akses terbuka melebihi batas waktu toleransi, sistem langsung memicu alert visual di peta 3D dalam <5 detik.
4. **Instant Incident Review** — Supervisor menerima notifikasi real-time di dashboard dan dapat langsung meninjau rekaman di lokasi kejadian melalui koordinat 3D.
5. **Compliance Export** — User mengekspor laporan standar **FHIR R4** untuk pembuktian kepatuhan operasional kepada BPOM secara instan.

---

## Data Flow

```
Safety officer mengunggah video/foto fasilitas
    ↓
pipeline/classify.py  →  Claude Vision: tag area types, K3 hazard signals
    ↓
pipeline/scene_graph.py  →  structured scene graph JSON
    ↓
pipeline/world_model.py  →  World Labs Marble API  →  .spz → Azure Blob Storage
    ↓
Spatial Command Center: model 3D ditampilkan di frontend
    ↓
Admin: Virtual Sensor Tagging — petakan ID sensor/kamera ke koordinat 3D
    ↓
Active Monitoring: YOLO (Modal A10G) + IoT sensor stream
    ↓
Anomali terdeteksi → agents/consensus.py (CSE — Azure OpenAI)
    ↓
iris_client.write_findings()  →  IRIS Secure Wallet (FHIR R4, ALCOA+)
    ↓
azure_pubsub_client.publish()  →  Azure Web PubSub → live alert panel (dashboard)
    ↓
/api/reports  →  PDF (ReportLab) atau FHIR R4 DiagnosticReport (on-demand)
```

---

## Analisis Komparatif

| Parameter Evaluasi | Status Quo (Manual) | VeSafe (Spatial Intelligence) | Dampak Bisnis |
|---|---|---|---|
| **Response Latency** | Reaktif; bergantung jadwal inspeksi fisik | Proaktif; deteksi instan <5 detik | Mencegah kerusakan molekuler pada batch sensitif |
| **Data Veracity** | Foto manual, rawan manipulasi & kehilangan metadata | Spatial Anchoring — data IoT terikat ke koordinat 3D | Menjamin kepatuhan ALCOA+ |
| **Compliance Audit** | 3–5 hari konsolidasi data manual | On-demand — ekspor FHIR R4 otomatis | Audit-readiness 24/7, hemat biaya administratif |
| **Asset Validation** | Verifikasi tata letak berkala/manual | Validasi otomatis via Digital Twin vs. regulasi | Desain fasilitas selalu sesuai standar GxP |

---

## Roadmap

- **Predictive Risk Scoring** — Integrasi Azure OpenAI untuk memprediksi potensi kebocoran suhu atau kegagalan alat berdasarkan pola historis data sensor *sebelum* anomali terjadi.
- **Digital Audit Passthrough** — Portal bagi auditor eksternal (BPOM/WHO) untuk melakukan inspeksi fasilitas secara virtual melalui 3D model, mengurangi kebutuhan kunjungan fisik dan mempercepat sertifikasi.
- **Dynamic Evacuation Routing** — Integrasi jalur evakuasi darurat yang dipandu AI berdasarkan lokasi ancaman (misal: kebocoran gas kimia) yang terdeteksi secara spasial.
