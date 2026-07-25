from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.auth.schemas import Token, UserLogin, UserOut, UserRegister
from backend.auth.service import AuthError, AuthService
from backend.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, auth: AuthService = Depends(get_auth_service)):
    try:
        return await auth.register(payload.email, payload.password, payload.display_name)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, auth: AuthService = Depends(get_auth_service)):
    try:
        token = await auth.authenticate(payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return current_user
