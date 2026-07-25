from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.project import ProjectCreate, ProjectOut
from backend.auth.dependencies import get_current_user
from backend.database import get_db
from backend.database.models import Project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.owner_id == current_user["id"]).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    project = Project(owner_id=current_user["id"], **payload.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project
