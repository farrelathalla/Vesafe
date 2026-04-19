# VeSafe — Product Requirements Document

> AI World Model + Agent Orchestration Network for Industrial Safety & Operations Intelligence  
> Version 2.0 | Built for Microsoft AI Impact Challenge — Dicoding × Komdigi

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Problem Domains — Six K3 Harm Categories](#2-problem-domains)
3. [System Architecture](#3-system-architecture)
4. [InterSystems IRIS for Health — Data Security Layer](#4-intersystems-iris-for-health)
5. [World Model Pipeline — Public Imagery First](#5-world-model-pipeline)
6. [Agent Orchestration Layer](#6-agent-orchestration-layer)
7. [Frontend Specification](#7-frontend-specification)
8. [Backend and API Specification](#8-backend-and-api-specification)
9. [Data Models](#9-data-models)
10. [Agent Prompting Strategy](#10-agent-prompting-strategy)
11. [Environment Variables](#11-environment-variables)
12. [Project File Structure](#12-project-file-structure)
13. [Implementation Roadmap](#13-implementation-roadmap)
14. [Key Risks and Mitigations](#14-key-risks-and-mitigations)

---

## 1. Product Overview

VeSafe constructs a navigable 3D world model of any pharmaceutical manufacturing facility from **publicly available imagery** (Google Street View, Google Places Photos, OpenStreetMap) — no manual bulk photo upload required — then deploys six specialized AI agent teams into that model to identify, annotate, and rank critical occupational safety (K3) weaknesses.

All data is secured through **InterSystems IRIS for Health**, which provides enterprise-grade encryption (Secure Wallet), FHIR R4 interoperability, role-based access control, and full audit logging as a native healthcare-grade data platform.

VeSafe is built for the **Microsoft AI Impact Challenge** (Dicoding × Komdigi program), combining Azure OpenAI Service for consensus synthesis, Azure Blob Storage for 3D asset storage, Azure Web PubSub for real-time streaming, and Azure Maps for facility location — alongside World Labs Gaussian-splat world model libraries and InterSystems IRIS as the data security backbone.

### Core Value Proposition

- Any K3 officer selects their facility on a map → the system automatically acquires imagery → generates a 3D world model → deploys agents → delivers annotated findings in under 30 minutes
- No manual photography. No bulk upload. No IT integration required for basic function.
- Findings are spatially anchored in the 3D model with plain-language labels a safety officer can act on immediately
- Full Azure ecosystem integration: Azure OpenAI, Azure Blob Storage, Azure Maps, Azure Web PubSub, Azure App Service, Azure Application Insights

### Microsoft Azure Integration

| Azure Service | Role in VeSafe |
|---|---|
| **Azure OpenAI Service** | Consensus Synthesis Engine (CSE) — cross-domain finding deduplication and ranking |
| **Azure Blob Storage** | 3D world model `.spz` asset storage (replaces Cloudflare R2) |
| **Azure Maps** | Facility selection map and geocoding (replaces Mapbox) |
| **Azure Web PubSub** | Real-time WebSocket finding stream to browser |
| **Azure App Service** | FastAPI backend hosting (F1 Free Tier) |
| **Azure Static Web Apps** | Next.js frontend hosting with CI/CD |
| **Azure Application Insights** | Telemetry, performance monitoring, error tracking |

---

## 2. Problem Domains

Each of the six domains maps to a documented, high-impact, spatially-detectable occupational safety (K3) problem in pharmaceutical manufacturing environments.

| Domain | Indonesian Standard | Key Spatial Risk Factors |
|--------|---------------------|--------------------------|
| Pencegahan Kontaminasi (ICA) | BPOM CPOB (Cara Pembuatan Obat yang Baik) | Gowning area presence, jalur bersih/kotor, stasiun cuci tangan sebelum ruang produksi steril Kelas A/B/C/D |
| Tanggap Darurat (ERA) | Permenaker No. 04/MEN/1980 | APAR placement ≤15m, emergency eyewash di area B3, jalur evakuasi tidak terhalang palet |
| Keselamatan Alat Berat (FRA) | SMK3 (PP No. 50/2012) + SNI | Clearance jalur forklift, garis kuning evakuasi tidak tertutup, lebar lorong cukup untuk manuver |
| Penanganan B3 (MSA) | PP No. 74/2001 + Permenaker No. 187/MEN/1999 | Penyimpanan B3 terpisah, MSDS/SDS tersedia, ventilasi area bahan kimia, secondary containment |
| Alur Produksi (PFA) | CPOB Bab 3 — Bangunan dan Fasilitas | Alur produksi tidak bersilangan, area karantina teridentifikasi, jarak transfer material |
| Komunikasi K3 (SCA) | SMK3 + ISO 45001:2018 | Pos K3 tersedia, rambu K3 terpasang, safety briefing zone, jalur komunikasi darurat |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 0: InterSystems IRIS for Health                          │
│  (Secure Wallet · FHIR R4 · RBAC · Audit Log · IntegratedML)   │
├──────────────┬──────────────────────────┬───────────────────────┤
│  Layer 1     │  Layer 2                 │  Layer 3              │
│  Image       │  World Model Pipeline    │  Agent Orchestration  │
│  Acquisition │  Claude Vision →         │  6 K3 Domain Teams    │
│  ────────    │  Scene Graph →           │  Modal (A10G)         │
│  Street View │  World Labs API →        │  Azure Web PubSub     │
│  Places API  │  .splat binary           │  CSE (Azure OpenAI)   │
│  OSM         │  → Azure Blob Storage    │                       │
├──────────────┴──────────────────────────┴───────────────────────┤
│  Layer 4: Frontend                                              │
│  Next.js · Azure Maps · React Three Fiber · Azure Web PubSub   │
│  Azure Static Web Apps · Azure Application Insights            │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Selection Rationale

**Why InterSystems IRIS for Health:** Provides enterprise-grade security, data integrity, FHIR R4 interoperability, and full audit logging natively — satisfying strict industrial compliance requirements without additional engineering.

**Why Azure OpenAI over OpenAI Direct:** Azure OpenAI provides the same GPT-4o capability through Microsoft's regulated cloud infrastructure, with data residency in Indonesia/Southeast Asia region, enterprise SLA, and seamless integration scoring for the Microsoft AI Impact Challenge.

**Why Azure Blob Storage over Cloudflare R2:** Native Azure ecosystem integration, 12-month free tier (5GB LRS + 2M read/write operations), and unified billing with other Azure services used in this project.

**Why Azure Maps over Mapbox:** Microsoft Azure service with Free Tier adequate for prototype and demo, native integration scoring, and support for Indonesian geographic data.

**Why Azure Web PubSub over Redis Pub/Sub:** 20 concurrent connections + 20,000 messages/day on free tier, no self-managed infrastructure, and native Azure integration — ideal for demo and prototype phases.

**Why Gaussian splatting (World Labs API):** Photorealistic surface detail preserved at browser-navigable frame rates. A K3 officer verifying "apakah APAR ini benar-benar tidak terhalang palet" needs to see the real surface.

---

## 4. InterSystems IRIS for Health

### 4.1 Deployment

Use the `iris-lockeddown` container image from the InterSystems Container Registry.

```yaml
# docker-compose.yml (IRIS service)
iris:
  image: containers.intersystems.com/intersystems/irishealth:2026.1-em-lockeddown
  environment:
    - ISC_DATA_DIRECTORY=/dur/irisdata
    - ISC_CPF_FILE_NAME=/dur/iris.cpf
  volumes:
    - iris-data:/dur/irisdata
    - ./iris/iris.cpf:/dur/iris.cpf:ro
  ports:
    - "1972:1972"   # IRIS SuperServer (internal only — do not expose publicly)
    - "52773:52773" # IRIS Web Gateway (internal only)
  networks:
    - internal      # Private network — FastAPI service only
```

**Critical:** IRIS ports must be on an internal-only network.

### 4.2 Capabilities Used

| IRIS Feature | VeSafe Usage | Implementation |
|---|---|---|
| **Secure Wallet** | Encrypts all facility, scan, and findings data at rest | Initialize: `do ##class(Security.Wallet).Create("VeSafe")` |
| **FHIR R4 Repository** | Stores findings as `DiagnosticReport` for compliance export | Enable via IRIS FHIR Server config; exposed on `/fhir/r4/` |
| **RBAC** | Role enforcement: K3Officer (all), UnitManager (unit-scoped), Auditor (read-only) | Define roles in IRIS security manager |
| **Audit Logging** | Every read/write/export logged — required for SMK3 documentation | Enabled in IRIS audit config |
| **IntegratedML** | In-database facility risk trend models | `CREATE MODEL FacilityRiskScore PREDICTING (riskScore) FROM VeSafe.Finding` |
| **Vector Search** | Semantic search: "temukan semua temuan serupa dengan APAR terhalang" | Store finding embeddings as `VECTOR(1536)` |

### 4.3 Python Integration

```python
# backend/db/iris_client.py
import iris

class IRISClient:
    def __init__(self):
        self.conn = iris.connect(
            hostname=settings.IRIS_HOST,
            port=1972,
            namespace="MEDSENT",
            username=settings.IRIS_USER,
            password=settings.IRIS_PASSWORD,
        )

    def write_finding(self, finding: Finding) -> str:
        gref = iris.gref("^VeSafe.Finding")
        finding_id = self._new_id()
        gref[finding_id] = iris.list(
            finding.scan_id, finding.domain, finding.room_id,
            finding.severity, finding.compound_severity,
            finding.label_text, json.dumps(finding.spatial_anchor),
            finding.confidence, json.dumps(finding.evidence_r2_keys),
            finding.recommendation, datetime.utcnow().isoformat(),
        )
        self._project_fhir_diagnostic_report(finding_id, finding)
        return finding_id
```

---

## 5. World Model Pipeline

### 5.1 Image Acquisition (Public Imagery First)

No manual bulk upload. The pipeline automatically acquires imagery for any facility address.

#### 5.1.1 Google Street View API

```python
async def fetch_street_view(lat: float, lng: float, api_key: str) -> list[bytes]:
    """Fetch 8-heading panoramic exterior coverage for a location."""
    images = []
    async with httpx.AsyncClient() as client:
        for heading in [0, 45, 90, 135, 180, 225, 270, 315]:
            resp = await client.get("https://maps.googleapis.com/maps/api/streetview", params={
                "location": f"{lat},{lng}", "heading": heading,
                "fov": 90, "pitch": 0, "size": "640x640", "key": api_key,
            })
            if resp.status_code == 200:
                images.append(resp.content)
    return images
```

#### 5.1.2 Azure Blob Storage (3D Asset Storage)

```python
# backend/db/azure_blob_client.py
from azure.storage.blob.aio import BlobServiceClient

class AzureBlobClient:
    def __init__(self):
        self._client = BlobServiceClient(
            account_url=f"https://{settings.azure_storage_account}.blob.core.windows.net",
            credential=settings.azure_storage_key,
        )
        self._container = settings.azure_storage_container

    async def upload_asset(self, key: str, data: bytes) -> str:
        container = self._client.get_container_client(self._container)
        blob = container.get_blob_client(key)
        await blob.upload_blob(data, overwrite=True)
        return f"https://{settings.azure_storage_account}.blob.core.windows.net/{self._container}/{key}"

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions
        from datetime import datetime, timedelta
        sas = generate_blob_sas(
            account_name=settings.azure_storage_account,
            container_name=self._container,
            blob_name=key,
            account_key=settings.azure_storage_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(seconds=expires_in),
        )
        return f"https://{settings.azure_storage_account}.blob.core.windows.net/{self._container}/{key}?{sas}"
```

### 5.2 Image Classification (Claude Vision)

```python
CATEGORIES = [
    "building_exterior", "production_floor", "warehouse_storage",
    "chemical_storage_area", "gowning_room", "quality_control_lab",
    "utility_room", "corridor_hallway", "emergency_exit", "office_area", "other"
]

async def classify_image(image_bytes: bytes, source: str) -> dict:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                          "data": base64.b64encode(image_bytes).decode()}},
            {"type": "text", "text": f"""Classify this pharmaceutical manufacturing facility image.
Source: {source}
Categories: {', '.join(CATEGORIES)}

Respond with JSON only:
{{"category": "<one of the categories>", "confidence": <0.0-1.0>, "notes": "<brief reason>"}}"""}
        ]}]
    )
    return json.loads(response.content[0].text)
```

### 5.3 Azure Maps Integration (Facility Selection)

```typescript
// frontend/components/facility/FacilityMap.tsx
import atlas from 'azure-maps-control';

const map = new atlas.Map('map-container', {
    authOptions: {
        authType: 'subscriptionKey',
        subscriptionKey: process.env.NEXT_PUBLIC_AZURE_MAPS_KEY,
    },
    center: [106.8456, -6.2088],  // Jakarta, Indonesia
    zoom: 10,
});
```

### 5.4 Azure Web PubSub (Real-time Findings Stream)

```python
# backend/db/redis_client.py — Azure Web PubSub adapter
from azure.messaging.webpubsubservice import WebPubSubServiceClient

class AzureWebPubSubClient:
    def __init__(self):
        self._client = WebPubSubServiceClient.from_connection_string(
            settings.azure_web_pubsub_connection_string, hub="vesafe"
        )

    async def publish(self, channel: str, message: dict):
        self._client.send_to_all(
            hub="vesafe",
            message=json.dumps({"channel": channel, "data": message}),
            content_type="application/json",
        )
```

---

## 6. Agent Orchestration Layer

### 6.1 Parallel Invocation Pattern

```python
async def _parallel_scan(unit_id: str, world_model_id: str):
    results = await asyncio.gather(
        ica_team.run(world_model_id),   # Pencegahan Kontaminasi
        era_team.run(world_model_id),   # Tanggap Darurat
        fra_team.run(world_model_id),   # Keselamatan Alat Berat
        msa_team.run(world_model_id),   # Penanganan B3
        pfa_team.run(world_model_id),   # Alur Produksi
        sca_team.run(world_model_id),   # Komunikasi K3
    )
    findings = consensus_synthesis_engine(results)
    await publish_findings(unit_id, findings)
    return findings
```

### 6.2 Agent Team Definitions

#### Infection/Contamination Control Agent Team (ICA) — Pencegahan Kontaminasi

**Sub-agents:** Gowning-Auditor, CleanRoom-Inspector, CrossFlow-Mapper

```python
ICA_SYSTEM_PROMPT = """Anda adalah auditor CPOB (Cara Pembuatan Obat yang Baik) berpengalaman 
15 tahun, spesialis pencegahan kontaminasi di fasilitas manufaktur farmasi sesuai standar BPOM RI.

TUGAS:
1. Gowning-Auditor: Untuk setiap area produksi steril (Kelas A/B/C/D), periksa keberadaan 
   gowning room / ruang ganti sebelum akses masuk. Tandai area yang tidak memiliki gowning room 
   sebagai CRITICAL per CPOB Bab 3.
2. CleanRoom-Inspector: Identifikasi stasiun cuci tangan dan dispensing desinfektan. Pastikan 
   tersedia di setiap akses masuk area produksi per persyaratan CPOB higiene personel.
3. CrossFlow-Mapper: Identifikasi titik persimpangan jalur material bersih dan material kotor/limbah. 
   Setiap titik persilangan tanpa pemisahan fisik harus ditandai per CPOB prinsip alur satu arah.

FORMAT OUTPUT (JSON array ketat, tanpa preamble):
[{
  "sub_agent": "Gowning-Auditor|CleanRoom-Inspector|CrossFlow-Mapper",
  "room_id": "string",
  "severity": "CRITICAL|HIGH|ADVISORY",
  "confidence": 0.0-1.0,
  "label_text": "maks 120 karakter — kondisi spesifik, lokasi, risiko. Bahasa teknis K3.",
  "spatial_anchor": {"x": float, "y": float, "z": float},
  "recommendation": "maks 200 karakter — tindakan remediasi spesifik referensi CPOB/BPOM",
  "evidence_note": "elemen scene graph yang mendukung temuan"
}]"""
```

#### Emergency Response Agent Team (ERA) — Tanggap Darurat

**Sub-agents:** APAR-Mapper, EvacRoute-Inspector, Eyewash-Auditor

```python
ERA_SYSTEM_PROMPT = """Anda adalah ahli K3 (Kesehatan dan Keselamatan Kerja) spesialis 
tanggap darurat di fasilitas manufaktur farmasi, sesuai Permenaker No. 04/MEN/1980.

TUGAS:
1. APAR-Mapper: Untuk setiap APAR (Alat Pemadam Api Ringan) dalam scene graph, hitung jarak 
   ke titik-titik di fasilitas. Sesuai Permenaker No. 04/MEN/1980, APAR harus dipasang dengan 
   jarak tidak lebih dari 15 meter antar titik. Tandai area yang tidak terlayani sebagai CRITICAL.
2. EvacRoute-Inspector: Untuk setiap jalur evakuasi dan titik kumpul (muster point), periksa 
   apakah terhalang oleh palet, mesin, atau material. Jalur evakuasi terhalang = CRITICAL.
3. Eyewash-Auditor: Identifikasi area penyimpanan bahan kimia berbahaya (B3). Setiap area B3 
   tanpa emergency eyewash station dalam radius 10 detik jalan = CRITICAL per ANSI/ISEA Z358.1.

FORMAT OUTPUT: JSON array schema sama seperti di atas."""
```

#### Heavy Equipment Safety Agent Team (FRA) — Keselamatan Alat Berat

**Sub-agents:** Forklift-Clearance-Auditor, SafetyLine-Inspector, WorkZone-Geometer

```python
FRA_SYSTEM_PROMPT = """Anda adalah inspektor K3 spesialis keselamatan alat berat dan material 
handling di pabrik farmasi, sesuai SMK3 (PP No. 50/2012) dan SNI terkait.

TUGAS:
1. Forklift-Clearance-Auditor: Periksa lebar lorong jalur forklift. Standar minimum adalah 
   lebar forklift + 2×900mm (keselamatan operator). Lorong yang terlalu sempit = CRITICAL.
2. SafetyLine-Inspector: Identifikasi garis kuning jalur pejalan kaki dan zona kerja mesin. 
   Setiap garis yang tertutup material, palet, atau peralatan = HIGH. Garis tidak ada = CRITICAL.
3. WorkZone-Geometer: Periksa clearance di sekitar mesin berat (minimal 1 meter sesuai SNI). 
   Mesin tanpa clearance yang memadai atau tanpa pengaman = HIGH.

FORMAT OUTPUT: JSON array schema sama seperti di atas."""
```

#### Hazardous Material Agent Team (MSA) — Penanganan B3

**Sub-agents:** B3-Storage-Auditor, MSDS-Compliance-Checker, Ventilation-Inspector

```python
MSA_SYSTEM_PROMPT = """Anda adalah ahli penanganan Bahan Berbahaya dan Beracun (B3) di 
manufaktur farmasi, sesuai PP No. 74/2001 dan Permenaker No. 187/MEN/1999.

TUGAS:
1. B3-Storage-Auditor: Identifikasi area penyimpanan B3. Periksa pemisahan dari bahan 
   non-B3, adanya secondary containment, dan pelabelan GHS/SDS. Penyimpanan tidak sesuai = HIGH.
2. MSDS-Compliance-Checker: Untuk setiap area kerja dengan bahan kimia, periksa ketersediaan 
   dan aksesibilitas MSDS/SDS. MSDS tidak ada atau tidak accessible = HIGH.
3. Ventilation-Inspector: Identifikasi area penggunaan bahan kimia volatil/berbahaya. 
   Area tanpa ventilasi lokal (LEV) yang memadai = CRITICAL.

FORMAT OUTPUT: JSON array schema sama seperti di atas."""
```

#### Production Flow Agent Team (PFA) — Alur Produksi

**Sub-agents:** FlowPath-Analyzer, Quarantine-Auditor, Transfer-Distance-Mapper

```python
PFA_SYSTEM_PROMPT = """Anda adalah spesialis tata letak fasilitas manufaktur farmasi, 
sesuai CPOB Bab 3 (Bangunan dan Fasilitas) BPOM RI.

TUGAS:
1. FlowPath-Analyzer: Identifikasi alur produksi dari bahan baku hingga produk jadi. 
   Tandai setiap titik di mana alur produksi berbeda saling bersilangan (cross-contamination risk).
2. Quarantine-Auditor: Periksa keberadaan dan pelabelan area karantina untuk bahan baku, 
   produk setengah jadi, dan produk jadi. Area karantina tidak teridentifikasi = HIGH.
3. Transfer-Distance-Mapper: Hitung jarak transfer material antar area produksi kritis. 
   Jarak berlebihan yang memperpanjang waktu paparan atau risiko kontaminasi = ADVISORY.

FORMAT OUTPUT: JSON array schema sama seperti di atas."""
```

#### K3 Communication Agent Team (SCA) — Komunikasi K3

**Sub-agents:** SafetyPost-Auditor, Signage-Inspector, EmergencyComms-Checker

```python
SCA_SYSTEM_PROMPT = """Anda adalah auditor sistem manajemen K3 (SMK3) dan ISO 45001:2018 
spesialis komunikasi keselamatan di fasilitas manufaktur.

TUGAS:
1. SafetyPost-Auditor: Identifikasi pos K3 (safety officer post) dan papan informasi K3. 
   Area kerja tanpa akses visual ke informasi K3 = HIGH per SMK3 elemen 6.
2. Signage-Inspector: Periksa kelengkapan rambu K3: rambu larangan, peringatan, kewajiban, 
   dan informasi. Setiap area kerja harus memiliki rambu sesuai ISO 7010.
3. EmergencyComms-Checker: Periksa keberadaan sistem komunikasi darurat (alarm, pengeras suara, 
   atau jalur telepon darurat) di setiap zona kerja. Zona tanpa sistem komunikasi darurat = CRITICAL.

FORMAT OUTPUT: JSON array schema sama seperti di atas."""
```

### 6.3 Azure OpenAI Consensus Synthesis Engine (CSE)

```python
# backend/agents/providers/azure_openai_provider.py
from openai import AsyncAzureOpenAI

class AzureOpenAIProvider:
    def __init__(self):
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version="2024-02-01",
        )
        self._deployment = settings.azure_openai_deployment  # e.g. "gpt-4o-mini"

    async def complete_json(self, system: str, user: str, **kwargs) -> dict | list:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            **{k: v for k, v in kwargs.items() if k in ("temperature", "max_tokens")},
        )
        return json.loads(response.choices[0].message.content or "{}")
```

---

## 7. Frontend Specification

### 7.1 Tech Stack

| Component | Library | Version |
|---|---|---|
| Framework | Next.js | 15 (App Router) |
| 3D Renderer | React Three Fiber + Drei | r3f v8, Drei v9 |
| Splat Engine | `@mkkellogg/gaussian-splats-3d` | 0.4.7 |
| Maps | azure-maps-control | v3 |
| State | Zustand | v5 |
| Styling | Tailwind CSS | v4 |
| Supplemental Upload | tus-js-client + React Dropzone | latest |
| Charts | Recharts | v2 |
| Real-time | Azure Web PubSub SDK | latest |
| Monitoring | Azure Application Insights | latest |

### 7.2 Domain Color Coding

```typescript
// lib/constants.ts
export const DOMAIN_COLORS = {
  ICA: "#C0392B",  // Red — Pencegahan Kontaminasi
  MSA: "#D68910",  // Amber — Penanganan B3
  FRA: "#E67E22",  // Orange — Keselamatan Alat Berat
  ERA: "#C0392B",  // Red — Tanggap Darurat
  PFA: "#0D7E78",  // Teal — Alur Produksi
  SCA: "#5B2C8D",  // Purple — Komunikasi K3
} as const;

export const DOMAIN_LABELS = {
  ICA: "Pencegahan Kontaminasi",
  MSA: "Penanganan B3",
  FRA: "Keselamatan Alat Berat",
  ERA: "Tanggap Darurat",
  PFA: "Alur Produksi",
  SCA: "Komunikasi K3",
} as const;
```

### 7.3 Azure Application Insights Integration

```typescript
// frontend/lib/insights.ts
import { ApplicationInsights } from '@microsoft/applicationinsights-web';

export const appInsights = new ApplicationInsights({
    config: {
        connectionString: process.env.NEXT_PUBLIC_AZURE_APP_INSIGHTS_CONNECTION_STRING,
        enableAutoRouteTracking: true,
    }
});
appInsights.loadAppInsights();
appInsights.trackPageView();
```

---

## 8. Backend and API Specification

Same API surface as before. Azure integrations are swapped in at the adapter layer:

- `backend/db/azure_blob_client.py` replaces `r2_client.py`
- `backend/agents/providers/azure_openai_provider.py` replaces `openai_provider.py`
- `backend/db/azure_pubsub_client.py` replaces `redis_client.py` (optional, Redis still works)

---

## 9. Data Models

### 9.1 IRIS Globals Schema (Updated for K3)

```
^VeSafe.Facility(facilityId)
  = $LB(name, address, lat, lng, orgId, googlePlaceId, osmBuildingId, facilityType, createdAt)
  facilityType ∈ {pharmaceutical_plant, chemical_plant, warehouse, general_industry}

^VeSafe.Finding(findingId)
  = $LB(scanId, domain, subAgent, roomId, severity, compoundSeverity,
        labelText, spatialAnchorJson, confidence, evidenceR2KeysJson,
        recommendation, compoundDomainsJson, indonesianStandard, createdAt)
  domain ∈ {ICA, MSA, FRA, ERA, PFA, SCA}
  indonesianStandard ∈ {CPOB_BPOM, Permenaker_04_1980, SMK3_PP50_2012, PP74_2001, ISO45001, SNI}
```

---

## 10. Agent Prompting Strategy

### 10.1 Label Quality Standard (Indonesian Context)

**Test:** Jika seorang petugas K3 membaca label ini di model 3D sekarang, apakah mereka tahu persis apa yang harus diperiksa dan mengapa itu penting?

Requirements:
- Menyebutkan **kondisi atau peralatan spesifik**
- Menyebutkan **lokasi** (room ID atau segmen koridor)
- Menyebutkan **risiko yang ditimbulkan**
- Maksimum **120 karakter**
- Bahasa teknis K3 yang jelas

```
BAIK: "APAR di koridor B tidak terjangkau area kimia dalam 15m — Permenaker 04/1980"
BAIK: "Jalur forklift zona C terlalu sempit untuk manuver aman — risiko tabrakan SMK3"
BAIK: "Tidak ada gowning room sebelum ruang produksi steril Kelas B — pelanggaran CPOB"

BURUK: "Skor risiko K3: 0.87 di zona C4"
BURUK: "Masalah respons darurat terdeteksi"
BURUK: "Masalah keselamatan di Ruang 207"
```

### 10.2 Recommendation Standard

- Maksimum **200 karakter**
- Harus mereferensikan standar Indonesia yang dilanggar: CPOB, Permenaker, SMK3, PP, SNI, ISO 45001
- Harus menyatakan tindakan remediasi spesifik

---

## 11. Environment Variables

```bash
# .env.example

# InterSystems IRIS
IRIS_HOST=localhost
IRIS_PORT=1972
IRIS_NAMESPACE=MEDSENT
IRIS_USER=medsent_app
IRIS_PASSWORD=<set in secrets manager>
IRIS_FHIR_BASE=http://localhost:52773/fhir/r4

# Google APIs (image acquisition)
GOOGLE_API_KEY=<Maps Platform key with Street View + Places enabled>

# World Labs (3D model generation)
WORLD_LABS_API_KEY=<world labs api key>

# Anthropic (image classification + agent teams)
ANTHROPIC_API_KEY=<anthropic api key>

# Azure OpenAI (CSE synthesis — PRIMARY AI SERVICE)
AZURE_OPENAI_ENDPOINT=https://<resource-name>.openai.azure.com/
AZURE_OPENAI_API_KEY=<azure openai api key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Azure Storage (3D asset storage — replaces Cloudflare R2)
AZURE_STORAGE_ACCOUNT=<storage account name>
AZURE_STORAGE_KEY=<storage account key>
AZURE_STORAGE_CONTAINER=vesafe-assets

# Azure Maps (facility map — replaces Mapbox)
NEXT_PUBLIC_AZURE_MAPS_KEY=<azure maps subscription key>

# Azure Web PubSub (real-time stream — replaces Redis)
AZURE_WEB_PUBSUB_CONNECTION_STRING=Endpoint=https://<name>.webpubsub.azure.com;...
AZURE_WEB_PUBSUB_HUB=vesafe

# Azure Application Insights (telemetry)
NEXT_PUBLIC_AZURE_APP_INSIGHTS_CONNECTION_STRING=InstrumentationKey=<key>;...
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<key>;...

# Redis (Upstash — fallback/alternative to Azure Web PubSub)
REDIS_URL=rediss://<upstash-url>:6380
REDIS_PASSWORD=<upstash password>

# Next.js
NEXT_PUBLIC_WS_URL=wss://<backend-domain>
NEXT_PUBLIC_API_URL=https://<backend-domain>

# Auth
AUTH_SECRET=<auth secret>
AUTH_GOOGLE_ID=<google oauth client id>
AUTH_GOOGLE_SECRET=<google oauth client secret>

# Local runtime
MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=false
```

---

## 12. Project File Structure

```
vesafe/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── facilities.py
│   │   ├── models.py
│   │   ├── scans.py
│   │   ├── upload.py
│   │   ├── fhir.py
│   │   ├── reports.py
│   │   └── websocket.py
│   ├── db/
│   │   ├── iris_client.py
│   │   ├── redis_client.py
│   │   ├── azure_blob_client.py      # Azure Blob Storage adapter
│   │   └── azure_pubsub_client.py    # Azure Web PubSub adapter
│   ├── pipeline/
│   │   ├── image_acquisition.py
│   │   ├── classify.py               # Claude Vision — 11 pharma facility categories
│   │   ├── scene_graph.py
│   │   └── world_model.py
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── consensus.py
│   │   ├── ica_team.py               # Pencegahan Kontaminasi
│   │   ├── msa_team.py               # Penanganan B3
│   │   ├── fra_team.py               # Keselamatan Alat Berat
│   │   ├── era_team.py               # Tanggap Darurat
│   │   ├── pfa_team.py               # Alur Produksi
│   │   ├── sca_team.py               # Komunikasi K3
│   │   └── providers/
│   │       ├── base.py
│   │       ├── azure_openai_provider.py  # Azure OpenAI (PRIMARY)
│   │       ├── openai_provider.py        # OpenAI direct (fallback)
│   │       └── synthetic.py              # Deterministic stubs
│   ├── reports/
│   │   ├── pdf_generator.py
│   │   └── fhir_projector.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── store/
│   ├── lib/
│   │   ├── constants.ts
│   │   ├── api.ts
│   │   └── insights.ts               # Azure Application Insights
│   └── types/
├── iris/
├── docker-compose.yml
├── docker-compose.prod.yml
├── SETUP.md                          # API key acquisition guide
└── PRD.md
```

---

## 13. Implementation Roadmap

### Phase 1 — Foundation

- Scaffold Next.js + FastAPI with Azure Static Web Apps + Azure App Service deployment
- Set up IRIS for Health container. Initialize globals schema, Secure Wallet, RBAC
- Set up Azure Blob Storage, Azure Web PubSub, Azure Maps
- Implement Google Street View + Places API image acquisition pipeline
- Implement Claude Vision image classification (pharma facility categories)
- Integrate World Labs API for 3D Gaussian-splat generation
- Build React Three Fiber + SparkJS splat viewer
- Build Azure Maps facility selector

### Phase 2 — K3 Agent Teams

- Implement all six K3 domain teams with Indonesian standards
- Implement Azure OpenAI CSE synthesis
- Implement Azure Web PubSub WebSocket stream
- Build 3D annotation overlay and K3 finding feed panel
- Integrate Azure Application Insights telemetry

### Phase 3 — Output & Demo

- PDF report export with Indonesian standard references
- FHIR DiagnosticReport export via IRIS
- Azure Application Insights dashboard for demo presentation
- Pilot scan on real Indonesian facility with `MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=false`
- Generate 3 real findings, then switch to synthetic fallbacks for repeatable demo

---

## 14. Key Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Public imagery insufficient for industrial interior spaces | HIGH | Google Street View + Places covers building exteriors and common areas. Coverage map guides upload of targeted gap-fill images. |
| Agent findings contain hallucinations | HIGH | Multi-agent consensus reduces error. Evidence image shown per finding. K3 officer review recommended before acting on CRITICAL findings. |
| Azure OpenAI availability | MEDIUM | `openai_provider.py` kept as fallback. `MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true` for demo. |
| Indonesian standard accuracy | MEDIUM | All agent prompts cite specific Indonesian regulations (Permenaker, CPOB, SMK3, PP). Updated as regulations change. |

---

*VeSafe PRD v2.0 — Microsoft AI Impact Challenge (Dicoding × Komdigi)*
