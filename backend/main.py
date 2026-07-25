from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agents import ResearchAgent, get_agent_manager
from backend.api import api_router
from backend.config import get_settings
from backend.logging_ import get_logger, setup_logging
from backend.scheduler import get_scheduler

settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Asta OS backend starting up | env=%s", settings.ENV)

    agent_manager = get_agent_manager()
    await agent_manager.register_agent(ResearchAgent())

    scheduler = get_scheduler()
    await scheduler.startup()

    yield

    await scheduler.shutdown()
    logger.info("Asta OS backend shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
