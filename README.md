# Lease Reviewer – ADK Sidecar Demo

A **minimum reproducible example** of a microservice AI system built with:

| Layer | Technology |
|---|---|
| Agent backend | [Google ADK](https://google.github.io/adk-docs/) (Python) |
| LLM | Gemini 2.5 Flash via [LiteLLM](https://docs.litellm.ai/) |
| PDF → Markdown | [Docling](https://github.com/docling-project/docling-serve) sidecar |
| API gateway | FastAPI |
| Frontend | Streamlit |
| Container orchestration | Docker Compose |
| Package management | [uv](https://docs.astral.sh/uv/) |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Docker Compose network                                          │
│                                                                  │
│  ┌──────────┐  upload PDF   ┌─────────┐  /run   ┌───────────┐   │
│  │ frontend │──────────────▶│   api   │────────▶│    adk    │   │
│  │  :8501   │◀──────────────│  :8001  │◀────────│   :8000   │   │
│  │Streamlit │  agent reply  │ FastAPI │  events │  ADK API  │   │
│  └──────────┘               └─────────┘         └─────┬─────┘   │
│                                                        │         │
│                               convert_pdf_to_markdown  │         │
│                                                        ▼         │
│                                                  ┌───────────┐   │
│                                                  │  docling  │   │
│                                                  │   :5001   │   │
│                                                  │  sidecar  │   │
│                                                  └───────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Agent hierarchy

```
root_agent  (orchestrator, LlmAgent)
│  tools: convert_pdf_to_markdown
│  → calls docling sidecar, stores Markdown in session state
│
└── checklist_agent  (sub-agent, LlmAgent)
       output_schema: LeaseInformation (Pydantic)
       → extracts structured data + lists missing clauses
```

---

## Quick-start

### 1. Prerequisites

- Docker & Docker Compose v2
- A [Google AI Studio API key](https://aistudio.google.com/apikey)

### 2. Clone & configure

```bash
git clone https://github.com/j-jayes/adk-sidecar-setup.git
cd adk-sidecar-setup

cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=<your key>
```

### 3. Create the uploads directory

```bash
mkdir -p uploads
```

### 4. Start the stack

```bash
docker compose up --build
```

> **First run:** Docling downloads its models (~2 GB) on first boot.
> The `adk` service waits for Docling to pass its health check before starting.

### 5. Open the app

| Service | URL |
|---|---|
| Streamlit frontend | <http://localhost:8501> |
| FastAPI docs | <http://localhost:8001/docs> |
| ADK API server | <http://localhost:8000> |
| Docling API | <http://localhost:5001/docs> |

---

## Project layout

```
adk-sidecar-setup/
├── .env.example              # Environment variable template
├── docker-compose.yml        # Full stack definition
├── uploads/                  # Shared volume for uploaded PDFs (git-ignored)
│
├── docling/
│   └── Dockerfile            # Docling sidecar (customisation placeholder)
│
├── adk_service/              # Google ADK agent
│   ├── Dockerfile
│   ├── pyproject.toml        # uv-managed dependencies
│   └── lease_reviewer/
│       ├── __init__.py       # Exposes root_agent for ADK discovery
│       ├── agent.py          # Orchestrator + checklist sub-agent
│       ├── schemas.py        # LeaseInformation Pydantic model
│       ├── settings.py       # Config loaded from .env via pydantic-settings
│       └── tools.py          # convert_pdf_to_markdown (calls Docling)
│
├── api/                      # FastAPI gateway
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── main.py
│
├── frontend/                 # Streamlit UI
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app.py
│   └── assets/
│       └── custom.css
│
└── tests/                    # Integration & end-to-end tests
    ├── generate_test_pdf.py  # Generates tests/test-lease.pdf with reportlab
    ├── test_services.sh      # Polls each service until healthy, then smoke-tests
    └── e2e_test.py           # Uploads a PDF and runs a full review via the API
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | *(required)* | Google AI Studio API key |
| `AGENT_MODEL` | `gemini/gemini-2.5-flash` | LiteLLM model string |
| `DOCLING_URL` | `http://docling:5001` | Docling service endpoint |
| `DOCLING_TIMEOUT` | `300` | PDF conversion timeout (seconds) |
| `UPLOAD_DIR` | `/uploads` | Path where PDFs are stored inside containers |

---

## Development workflow

### Run the ADK service locally (outside Docker)

```bash
cd adk_service
uv sync
cp ../.env .env   # or export GOOGLE_API_KEY directly

uv run adk web --host 0.0.0.0 --port 8000 .
# Opens the ADK dev UI at http://localhost:8000
```

### Run the frontend locally

```bash
cd frontend
uv sync
API_URL=http://localhost:8001 uv run streamlit run app.py
```

---

## Open questions / next steps

The following items could be developed further depending on requirements:

1. **Authentication** – The demo has no auth. A real deployment should add
   OAuth2 / API-key protection on the FastAPI gateway.

2. **Streaming responses** – The ADK supports SSE streaming (`/run_sse`).
   Wiring this through to Streamlit (`st.write_stream`) would give a better
   UX for long responses.

3. **Session persistence** – ADK uses in-memory sessions by default.
   For production, configure a `DatabaseSessionService` (e.g. Cloud Firestore
   or PostgreSQL) so sessions survive restarts.

4. **Artefact storage** – The converted Markdown is stored in session state.
   For larger documents, consider using ADK's `ArtifactService` to store and
   retrieve blobs, keeping session state small.

5. **Multi-jurisdiction support** – The checklist prompt is generic.
   Different countries have different mandatory lease terms (e.g. EPC ratings
   in the UK, habitability requirements in the US).  The prompt could be
   extended with jurisdiction-specific checklists loaded from a config file.

6. **GPU-accelerated Docling** – The demo uses the CPU image.
   For high-throughput use, switch to `docling-serve-cu124` and adjust
   resource limits accordingly.

7. **Tests** – Basic integration tests are in `tests/` (health checks +
   end-to-end PDF review via `e2e_test.py`).  Unit tests for the Pydantic
   schemas and the API gateway, plus an ADK eval set, would be natural next
   additions.

8. **CI/CD** – A GitHub Actions workflow for Docker image builds and linting
   would be straightforward to add.

---

<<<<<<< HEAD
=======
## Architecture presentation (Quarto RevealJS)

The repository includes a slide deck for onboarding and demo walkthroughs:

- Source: `docs/index.qmd`
- Rendered output: `docs/index.html`
- Frontend screenshots: `docs/assets/screenshots/`
- Screenshot capture helper (R/webshot2): `docs/scripts/capture_screenshots.R`

Render locally:

```bash
quarto render docs/index.qmd
```

Publish to GitHub Pages:

```bash
quarto publish gh-pages docs/index.qmd --no-browser
```

If this is the first publish for the repository, ensure a `gh-pages` branch
exists on the remote before running the publish command.

---

>>>>>>> gh-pages
## Licence

Apache 2.0 – see [LICENSE](LICENSE).