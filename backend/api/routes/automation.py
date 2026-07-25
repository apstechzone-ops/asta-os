from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.automation.service import AutomationService

router = APIRouter(prefix="/automation", tags=["automation"])


def get_automation_service() -> AutomationService:
    return AutomationService()


class RunCommandRequest(BaseModel):
    shell: str  # "cmd" | "powershell"
    command: str
    timeout: int = 30


class ClipboardWriteRequest(BaseModel):
    content: str


class FileWriteRequest(BaseModel):
    path: str
    content: str


class BrowserOpenRequest(BaseModel):
    url: str


@router.post("/run")
async def run_command(
    req: RunCommandRequest,
    automation: AutomationService = Depends(get_automation_service),
    _current_user: dict = Depends(get_current_user),
):
    return await automation.run_command(req.shell, req.command, req.timeout)


@router.get("/clipboard")
async def read_clipboard(
    automation: AutomationService = Depends(get_automation_service),
    _current_user: dict = Depends(get_current_user),
):
    return {"content": await automation.read_clipboard()}


@router.post("/clipboard")
async def write_clipboard(
    req: ClipboardWriteRequest,
    automation: AutomationService = Depends(get_automation_service),
    _current_user: dict = Depends(get_current_user),
):
    await automation.write_clipboard(req.content)
    return {"status": "written"}


@router.get("/fs/list")
async def list_dir(
    path: str,
    automation: AutomationService = Depends(get_automation_service),
    _current_user: dict = Depends(get_current_user),
):
    return await automation.filesystem.list_dir(path)


@router.get("/fs/read")
async def read_file(
    path: str,
    automation: AutomationService = Depends(get_automation_service),
    _current_user: dict = Depends(get_current_user),
):
    return {"content": await automation.filesystem.read_file(path)}


@router.post("/fs/write")
async def write_file(
    req: FileWriteRequest,
    automation: AutomationService = Depends(get_automation_service),
    _current_user: dict = Depends(get_current_user),
):
    await automation.filesystem.write_file(req.path, req.content)
    return {"status": "written"}


@router.post("/browser/open")
async def open_url(
    req: BrowserOpenRequest,
    automation: AutomationService = Depends(get_automation_service),
    _current_user: dict = Depends(get_current_user),
):
    ok = await automation.browser.open_url(req.url)
    return {"opened": ok}
