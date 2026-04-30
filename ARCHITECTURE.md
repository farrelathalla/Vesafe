# Architecture

VeSafe is organized into four legible layers:

1. `frontend/`
   Next.js 15 App Router UI for facility onboarding, manual photo upload, world model viewing, and report export. Uses Azure Application Insights for telemetry.
2. `backend/`
   FastAPI APIs, world-model pipeline stages, six K3 domain agent teams, consensus synthesis (Azure OpenAI), and export generation.
3. `iris/`
   Deployment and first-run configuration for InterSystems IRIS for Health.
4. `docs/`
   Repository knowledge base. Source of truth for architecture, plans, product specs, quality, reliability, and security guidance.

## Package Boundaries

- `backend/api/`
  Transport layer only. Keep HTTP and WebSocket concerns here.
- `backend/db/`
  Persistence adapters. `iris_client.py`, `redis_client.py`, and `azure_blob_client.py` define swap-friendly seams.
- `backend/pipeline/`
  Image classification, scene-graph extraction, and world-model generation from manually uploaded photos.
- `backend/agents/`
  Six K3 domain teams, prompts, consensus synthesis, and scan orchestration.
- `backend/agents/providers/`
  LLM provider adapters: `azure_openai_provider.py` (primary), `openai_provider.py` (fallback), `synthetic.py` (no-key stubs).
- `backend/reports/`
  PDF and FHIR projection logic.
- `frontend/components/`
  Route-independent UI building blocks grouped by viewer, findings, facility, and shared UI.
- `frontend/lib/`
  API client, Azure Application Insights setup.

## Azure Integration

| Layer | Azure Service | Adapter |
|---|---|---|
| LLM (CSE) | Azure OpenAI | `agents/providers/azure_openai_provider.py` |
| Asset storage | Azure Blob Storage | `db/azure_blob_client.py` |
| Real-time stream | Azure Web PubSub | `db/redis_client.py` (adapter) |
| Telemetry | Azure Application Insights | `frontend/lib/insights.ts` |
| Backend hosting | Azure App Service | docker-compose.prod.yml |
| Frontend hosting | Azure Static Web Apps | GitHub Actions CI/CD |

## Development Notes

- Current persistence is in-memory for local determinism, but public interfaces mirror the PRD's IRIS-backed behavior.
- `MEDSENTINEL_IRIS_MODE=native` switches the persistence seam to the InterSystems Native SDK.
- LLM provider selection: Azure OpenAI → OpenAI direct → Synthetic, controlled by `get_llm_provider()` in `agents/providers/__init__.py`.
- `MEDSENTINEL_USE_SYNTHETIC_FALLBACKS=true` forces synthetic K3 findings — use for repeatable demos after real scan.
