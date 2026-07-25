#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

echo "Starting infra (postgres, chromadb, ollama)..."
docker compose up -d postgres chromadb ollama

echo "Installing backend deps..."
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

echo "Installing frontend deps..."
(cd frontend && npm install)

echo "Done. Run 'python -m backend.main' and 'npm run electron:dev' (in frontend/) in separate terminals."
