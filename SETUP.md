# VeSafe — Setup Guide

Complete guide to getting all API keys, configuring Azure services, running VeSafe with live keys, and switching to synthetic fallbacks for repeatable demos.

---

## Table of Contents

1. [Azure Services Setup](#1-azure-services-setup)
2. [Google APIs Setup](#2-google-apis-setup)
3. [World Labs API](#3-world-labs-api)
4. [Anthropic Claude API](#4-anthropic-claude-api)
5. [InterSystems IRIS Setup](#5-intersystems-iris-setup)
6. [Running with Live Keys (3 Real Results)](#6-running-with-live-keys)
7. [Switching to Synthetic Fallbacks](#7-switching-to-synthetic-fallbacks)
8. [Environment Variable Reference](#8-environment-variable-reference)

---

## 1. Azure Services Setup

### 1.1 Create a Resource Group

```bash
az login
az group create --name vesafe-rg --location southeastasia
```

### 1.2 Azure OpenAI Service (PRIMARY — required for AI scoring)

1. Go to **Azure Portal** → Search "Azure OpenAI" → Create
2. Region: `Southeast Asia` (or `East Asia` if unavailable)
3. After deployment, go to **Azure OpenAI Studio** → Deployments → Create
4. Deploy model: **`gpt-4o-mini`** (lowest cost, sufficient for CSE)
5. Note the deployment name you chose (e.g. `gpt-4o-mini`)
6. Get credentials: **Keys and Endpoint** → copy **Key 1** and **Endpoint**

```bash
# .env values
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<Key 1 from Keys and Endpoint>
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

**Cost estimate:** ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens. One full scan costs < $0.05.

### 1.3 Azure Blob Storage (3D asset storage)

```bash
# Create storage account
az storage account create \
  --name vesafestorage \
  --resource-group vesafe-rg \
  --location southeastasia \
  --sku Standard_LRS

# Create container
az storage container create \
  --name vesafe-assets \
  --account-name vesafestorage \
  --public-access off
```

Get the access key: **Azure Portal** → Storage Account → **Access keys** → copy **key1**

```bash
AZURE_STORAGE_ACCOUNT=vesafestorage
AZURE_STORAGE_KEY=<key1 from Access keys>
AZURE_STORAGE_CONTAINER=vesafe-assets
```

**Free tier:** 5 GB LRS storage + 2M read/write operations for 12 months.

### 1.4 Azure Maps (facility map)

```bash
az maps account create \
  --name vesafe-maps \
  --resource-group vesafe-rg \
  --sku G2
```

Get key: **Azure Portal** → Azure Maps account → **Authentication** → Primary Key

```bash
NEXT_PUBLIC_AZURE_MAPS_KEY=<Primary Key>
```

**Free tier:** 250,000 map tile requests/month — more than sufficient for prototype and demo.

### 1.5 Azure Web PubSub (real-time WebSocket stream)

```bash
az webpubsub create \
  --name vesafe-pubsub \
  --resource-group vesafe-rg \
  --sku Free_F1
```

Get connection string: **Azure Portal** → Web PubSub → **Keys** → Connection string (Primary)

```bash
AZURE_WEB_PUBSUB_CONNECTION_STRING=Endpoint=https://vesafe-pubsub.webpubsub.azure.com;AccessKey=<key>;Version=1.0;
AZURE_WEB_PUBSUB_HUB=vesafe
```

**Free tier:** 20 concurrent connections, 20,000 messages/day — ideal for demo.

### 1.6 Azure Application Insights (telemetry)

```bash
az monitor app-insights component create \
  --app vesafe-insights \
  --location southeastasia \
  --resource-group vesafe-rg \
  --application-type web
```

Get connection string: **Azure Portal** → Application Insights → **Overview** → Connection String

```bash
NEXT_PUBLIC_AZURE_APP_INSIGHTS_CONNECTION_STRING=InstrumentationKey=<key>;IngestionEndpoint=https://...
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<key>;IngestionEndpoint=https://...
```

**Free:** Application Insights has a generous free tier (5 GB/month data ingestion).

---

## 2. Google APIs Setup

### 2.1 Enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Go to **APIs & Services** → **Enable APIs and Services**
4. Enable these three APIs:
   - **Maps Static API** (Street View)
   - **Places API** (interior photos)
   - **Geocoding API** (address to coordinates)

### 2.2 Create API Key

1. **APIs & Services** → **Credentials** → **Create Credentials** → **API Key**
2. Restrict the key: **API restrictions** → select the three APIs above
3. Copy the key

```bash
GOOGLE_API_KEY=<your api key>
```

**Cost estimate:** ~$0.007/image × 16 images = ~$0.11 per facility. First $200/month free.

---

## 3. World Labs API

1. Go to [worldlabs.ai](https://worldlabs.ai) and create an account
2. Navigate to your **API Settings** / Dashboard
3. Create an API key
4. Note: World Labs Marble API is required for actual 3D model generation. Without it, use `MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true`.

```bash
WORLD_LABS_API_KEY=<your world labs api key>
WORLD_LABS_API_BASE=https://api.worldlabs.ai
```

---

## 4. Anthropic Claude API

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create account / log in
3. **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-`)

```bash
ANTHROPIC_API_KEY=sk-ant-<your key>
```

**Cost estimate:** Image classification uses Claude claude-sonnet-4-5. ~$0.003 per image × 50 images = ~$0.15 per facility scan. Agent teams use text-only mode in fallback mode.

---

## 5. InterSystems IRIS Setup

IRIS runs in Docker. For local development, use the community edition (free):

```bash
# Pull community image
docker pull intersystems/irishealth-community:latest-cd

# Or start via docker compose (recommended)
docker compose up iris -d

# Wait for initialization (~30 seconds)
docker compose logs iris | grep -i "startup"
```

IRIS credentials are set in `.env`:
```bash
IRIS_HOST=localhost
IRIS_PORT=1972
IRIS_NAMESPACE=MEDSENT
IRIS_USER=medsent_app
IRIS_PASSWORD=<choose a strong password>
```

The `iris/init.sh` script runs automatically on first start and creates the MEDSENT namespace, Secure Wallet, RBAC roles, and FHIR endpoint.

---

## 6. Running with Live Keys

After filling in all keys in `.env`:

```bash
# Ensure MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=false
grep SYNTHETIC .env

# Start infrastructure
docker compose up iris -d

# Start backend
source .venv/bin/activate
./scripts/start-backend.sh

# In another terminal, start frontend
cd frontend && npm run dev
```

### Get 3 Real Scan Results

1. Open `http://localhost:3000`
2. Go to **New Facility** and search for a pharmaceutical facility in Indonesia
   - Example: "Pabrik farmasi Karawang" or "Kimia Farma Plant Bandung"
3. Click **Acquire Imagery** — waits ~30s while Google APIs + World Labs run
4. Click **Run K3 Scan** — six agent teams run in parallel (~2-5 minutes)
5. View findings in the 3D model with K3 annotations
6. Repeat for 2 more facilities
7. Export PDF reports for each

After getting 3 real results, **save the scan IDs** — the synthetic fallback will return similar structured data for demo purposes.

---

## 7. Switching to Synthetic Fallbacks

After generating real results once, switch to synthetic mode for repeatable demos that don't consume API credits:

```bash
# In .env, set:
MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true
```

In synthetic mode:
- No calls to Google APIs, World Labs, Anthropic, or Azure OpenAI
- Returns deterministic K3 findings (APAR missing, gowning room issues, forklift clearance, etc.)
- All UI flows work normally: 3D viewer, findings panel, PDF export, FHIR export
- Azure Application Insights still tracks telemetry (the SDK loads independently)
- IRIS storage still works for persistence demo

**To re-enable live mode:** Set `MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=false` and restart the backend.

---

## 8. Environment Variable Reference

| Variable | Required | Description |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | Yes (for live AI) | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_KEY` | Yes (for live AI) | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | Yes | Model deployment name (e.g. `gpt-4o-mini`) |
| `AZURE_STORAGE_ACCOUNT` | Yes (for live) | Azure Blob Storage account name |
| `AZURE_STORAGE_KEY` | Yes (for live) | Azure Blob Storage access key |
| `AZURE_STORAGE_CONTAINER` | Yes | Container name (default: `vesafe-assets`) |
| `AZURE_WEB_PUBSUB_CONNECTION_STRING` | No | Azure Web PubSub for real-time stream |
| `AZURE_WEB_PUBSUB_HUB` | No | Hub name (default: `vesafe`) |
| `NEXT_PUBLIC_AZURE_MAPS_KEY` | Yes (for map) | Azure Maps subscription key |
| `NEXT_PUBLIC_AZURE_APP_INSIGHTS_CONNECTION_STRING` | No | App Insights connection string |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | No | App Insights for backend |
| `GOOGLE_API_KEY` | Yes (for imagery) | Google Maps Platform key |
| `WORLD_LABS_API_KEY` | Yes (for 3D model) | World Labs Marble API key |
| `ANTHROPIC_API_KEY` | Yes (for agents) | Anthropic Claude API key |
| `OPENAI_API_KEY` | No | OpenAI direct fallback key |
| `IRIS_HOST` | Yes | IRIS hostname |
| `IRIS_PASSWORD` | Yes | IRIS app user password |
| `REDIS_URL` | No | Redis fallback for pub/sub |
| `MEDSENTINEL_USE_SYNTHETIC_FALLBACKS` | No | `true` = skip all external APIs |

### Minimum Keys for Live Demo

For a fully live demo with Azure AI scoring:

```bash
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
NEXT_PUBLIC_AZURE_MAPS_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
WORLD_LABS_API_KEY=...
```

### Keys for Synthetic Demo (Zero API Cost)

```bash
MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true
NEXT_PUBLIC_AZURE_MAPS_KEY=...  # still needed for map tiles
NEXT_PUBLIC_AZURE_APP_INSIGHTS_CONNECTION_STRING=...  # optional but good for demo
```
