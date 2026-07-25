# Asta OS

AI Operating System — modular backend (FastAPI), futuristic Electron/React frontend.

## Quick Start

```bash
cp .env.example .env
docker compose up -d postgres chromadb ollama
cd backend && pip install -r requirements.txt --break-system-packages
alembic upgrade head
python -m backend.main

cd frontend && npm install
npm run electron:dev
```

## Backend Modules

`database` `memory` `planner` `tools` `auth` `voice` `automation` `rag` `google_workspace` `agents` `scheduler` `api` `config` `logging_` `shared`

Each is independent and depends only on the interfaces in its `interface.py` (or `backend/shared/module_base.py`).

## Tests

```bash
cd backend && pytest ../tests -v
```

See `docs/` for architecture notes.

