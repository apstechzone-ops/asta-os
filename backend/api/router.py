from fastapi import APIRouter

from backend.api.routes import (
    agents,
    ai_providers,
    auth,
    automation,
    google,
    memory,
    planner,
    projects,
    rag,
    scheduler,
    system,
    tasks,
    voice,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(memory.router)
api_router.include_router(planner.router)
api_router.include_router(voice.router)
api_router.include_router(automation.router)
api_router.include_router(rag.router)
api_router.include_router(google.router)
api_router.include_router(agents.router)
api_router.include_router(scheduler.router)
api_router.include_router(tasks.router)
api_router.include_router(projects.router)
api_router.include_router(ai_providers.router)
