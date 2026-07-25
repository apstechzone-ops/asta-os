from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.database import get_db
from backend.google_workspace import (
    CalendarService,
    DocsService,
    DriveService,
    GmailService,
    build_auth_url,
    exchange_code_for_credentials,
    load_credentials,
    save_credentials,
)

router = APIRouter(prefix="/google", tags=["google"])


async def _get_credentials(db: AsyncSession, user_id: str):
    creds = await load_credentials(db, user_id)
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Google account not connected. Call /google/auth-url first.",
        )
    return creds


@router.get("/auth-url")
async def auth_url(current_user: dict = Depends(get_current_user)):
    return {"url": build_auth_url(state=current_user["id"])}


@router.get("/status")
async def connection_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    creds = await load_credentials(db, current_user["id"])
    return {"connected": creds is not None}


@router.get("/callback")
async def callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    credentials = exchange_code_for_credentials(code)
    await save_credentials(db, user_id=state, credentials=credentials)
    return {"status": "connected"}


@router.get("/gmail/messages")
async def gmail_messages(
    q: str = "",
    max_results: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    creds = await _get_credentials(db, current_user["id"])
    return await GmailService(creds).list_messages(q, max_results)


@router.get("/drive/files")
async def drive_files(
    q: str = "",
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    creds = await _get_credentials(db, current_user["id"])
    return await DriveService(creds).list_files(q)


@router.get("/calendar/events")
async def calendar_events(
    max_results: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    creds = await _get_credentials(db, current_user["id"])
    return await CalendarService(creds).list_upcoming_events(max_results)


class CreateDocRequest(BaseModel):
    title: str
    content: str = ""


@router.post("/docs/create")
async def docs_create(
    req: CreateDocRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    creds = await _get_credentials(db, current_user["id"])
    return await DocsService(creds).create_document(req.title, req.content)
