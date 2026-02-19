# AutoPilotOps

Self-improving AI DevOps engineer demo. FastAPI backend + React frontend.

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
npm install
npm run dev
```

Open `http://localhost:5173`.
