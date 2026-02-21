# AutoPilotOps

Self-improving AI DevOps engineer demo. FastAPI backend + React frontend.

## Configuration

Copy `.env.example` to `.env` and adjust values.

Backend settings are loaded via `pydantic-settings`:

- `ENV`: environment name (default: `development`)
- `LOG_LEVEL`: optional Python log level override (defaults by ENV: development=`DEBUG`, production=`INFO`)
- `ALLOWED_ORIGINS`: comma-separated explicit CORS origins (required, wildcard `*` is rejected; production requires `https://` non-localhost origins)
- `API_KEY`: API key for mutating endpoints (`/simulate_incident`, `/run_pipeline`); required in production
- `LLM_MODEL`: model label used for diagnosis generation and metrics
- `LLM_TIMEOUT_SECONDS`: per-attempt timeout for LLM calls
- `LLM_MAX_RETRIES`: retry count for LLM calls before fallback
- `LLM_RETRY_BACKOFF_MS`: delay between retries
- `MEMORY_BACKEND`: `sqlite`, `json`, or `auto` (default: `sqlite`)
- `MEMORY_DB_URL`: SQLAlchemy DB URL for SQLite memory store
- `MEMORY_STORE_PATH`: path to the memory JSON file
- `MAX_REQUEST_SIZE_BYTES`: request body size limit for mutating endpoints
- `RATE_LIMIT_REQUESTS_PER_WINDOW`: max mutating requests per IP in a window
- `RATE_LIMIT_WINDOW_SECONDS`: rate-limit window size in seconds
- `AUTONOMY_ENABLED`: starts autonomous control loop at API startup
- `AUTONOMY_POLL_SECONDS`: interval for real-time telemetry checks
- `AUTONOMY_MAX_RUNS`: in-memory retention of autonomous run history
- `LIGHTDASH_API_URL`: real-time metrics source endpoint
- `LIGHTDASH_API_KEY`: optional auth for Lightdash endpoint
- `LIGHTDASH_PROJECT`: project label for telemetry payloads
- `AIRIA_API_URL`: endpoint for autonomous action dispatch
- `AIRIA_API_KEY`: optional auth for Airia endpoint
- `MODULATE_API_URL`: endpoint for voice/alert delivery
- `MODULATE_API_KEY`: optional auth for Modulate endpoint
- `MODULATE_VOICE`: optional voice/profile id for Modulate calls


Production behavior switches by `ENV`:

- `ENV=production`: docs/OpenAPI disabled (`/docs`, `/redoc`, `/openapi.json` unavailable)
- `ENV=production`: `API_KEY` required
- `ENV=production`: strict HTTPS non-localhost CORS enforcement
- Logging defaults to `INFO` in production and `DEBUG` in development unless `LOG_LEVEL` is set

Frontend optional env vars:

- `VITE_BACKEND_URL`: frontend backend base URL (in production Docker, defaults to `/api` via Nginx reverse proxy)
- `VITE_API_KEY`: sent as `X-API-Key` header to backend
- `VITE_ELEVENLABS_API_KEY`: enables ElevenLabs TTS
- `VITE_ELEVENLABS_VOICE_ID`: ElevenLabs voice id

## Security Middleware

Mutating endpoints (`POST`, `PUT`, `PATCH`, `DELETE`) pass through middleware that enforces:

- API key validation (`X-API-Key`) when `API_KEY` is configured
- Request size guard using `MAX_REQUEST_SIZE_BYTES`
- Per-IP rate limiting using `RATE_LIMIT_REQUESTS_PER_WINDOW` and `RATE_LIMIT_WINDOW_SECONDS`

Error responses are explicit:

- `401`: missing/invalid API key for mutating endpoint
- `413`: request body exceeded configured size limit
- `429`: per-IP rate limit exceeded for mutating endpoints

## API Response Schema

All responses include a `request_id`.

Success response shape:

```json
{
  "request_id": "uuid-or-forwarded-id",
  "data": { "..." : "endpoint payload" }
}
```

Error response shape:

```json
{
  "request_id": "uuid-or-forwarded-id",
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": []
  }
}
```

The server also returns `X-Request-ID` response header. Unhandled exceptions return a generic `500` error message and do not expose stack traces to clients.

## Operational Endpoints

- `GET /health`: liveness check
- `GET /ready`: readiness check (verifies memory store accessibility)
- `GET /autonomy/status`: autonomous loop status + learning metrics
- `GET /autonomy/runs`: recent autonomous runs and sponsor-tool actions
- `POST /autonomy/run_once`: force one autonomous telemetry check/tick

`/ready` returns `503` with structured error details when dependencies are not accessible.

## Logging

Backend logs are structured JSON and include request metadata:

- `request_id`
- `method`
- `path`
- `status_code`
- `duration_ms`

Pipeline runs emit per-step timing logs under `timings_ms` and a final `pipeline_completed` event with total duration.
LLM calls are wrapped with timeout/retry and deterministic fallback, and emit safe logs/metrics (no prompt contents).

## Memory Persistence

Memory persistence uses a repository layer:

- Primary: SQLite via SQLAlchemy (`MEMORY_BACKEND=sqlite`)
- Development fallback: if SQLite is unavailable in `ENV=development`, backend falls back to JSON file storage (`MEMORY_STORE_PATH`)

Repository tests live under `backend/tests`.

## Hackathon Requirements Coverage

AutoPilotOps now supports strict autonomous operation with sponsor-tool wiring:

- Real-time data ingestion: `LightdashClient` pulls live telemetry (or deterministic fallback simulation)
- Meaningful autonomous action: anomaly thresholds trigger full remediation pipeline
- Continuous self-improvement: memory store reuse drives memory-hit rate and learning score
- Sponsor tools: Lightdash (telemetry), Airia (action dispatch), Modulate (voice summary/alerts)

## Backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

API docs: `http://localhost:8000/docs`

## Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`.

## Quality Tooling

Backend checks:

- `ruff check backend/app backend/tests`
- `pytest -q` (run from `backend/`)
- `python -m compileall app` (run from `backend/`)

Pre-commit setup:

```bash
pip install pre-commit
pre-commit install
```

CI runs on GitHub Actions for backend and frontend lint/test/build checks.

## Docker Compose

Run full stack with Docker:

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:5173`
- Backend API (direct): `http://localhost:8000`
- Backend API (recommended via frontend origin): `http://localhost:5173/api`
- Backend docs: `http://localhost:8000/docs`

Container healthchecks:

- Backend uses `GET /ready`
- Frontend uses `GET /health` (Nginx endpoint)
