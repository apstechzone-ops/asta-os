# Architecture

## Principle

Every backend module exposes an `interface.py` (ABC). Consumers (Planner, API routes)
depend on the interface, never the concrete class. `backend/shared/module_base.py`
defines the common lifecycle contract (`startup`, `shutdown`, `health`).

## Module map

| Module | Responsibility | Depends on (interfaces only) |
|---|---|---|
| `database` | SQLAlchemy models + async session | — |
| `ai_providers` | model-agnostic LLM access: Ollama/OpenRouter/Cloudflare, failover, rule-based routing, usage logging | `database` (usage_logger only) |
| `memory` | short/long-term memory, vector + structured search, conversation trimming | `database` |
| `tools` | tool registry/execution | — |
| `planner` | intent → memory/RAG context (PromptBuilder) → tool decision → streamed response via AIRouter | `memory`, `tools`, `ai_providers`, `rag` |
| `auth` | bcrypt + JWT, register/login/me | `database` |
| `voice` | Whisper STT / Piper TTS | — |
| `automation` | CMD/PowerShell/FS/Clipboard/Browser | — |
| `rag` | chunked ingestion + Chroma retrieval | — |
| `google_workspace` | OAuth2 + Gmail/Drive/Calendar/Docs | `database` (credential storage) |
| `agents` | agent registry + capability-based dispatch | — |
| `scheduler` | APScheduler once/cron jobs | — |
| `api` | FastAPI routers, one per module | all of the above |

## Request flow (chat)

`POST /api/v1/planner/chat` → `get_current_user` (auth) → `PlannerService.handle_message`
→ `MemoryInterface.add_short_term` / `get_recent_messages` → tool-call decision via Ollama
→ optional `ToolManagerInterface.execute` → streamed final response via Ollama →
`MemoryInterface.add_short_term` (assistant turn).

## Data stores

- **Postgres**: users, settings, projects, tasks, planner_state, agent_metadata, conversation_sessions, messages
- **ChromaDB**: two collections — `asta_memory` (long-term memory) and `asta_rag` (document chunks)
