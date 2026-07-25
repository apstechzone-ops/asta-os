from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.interface import AuthInterface
from backend.auth.security import create_access_token, decode_access_token, hash_password, verify_password
from backend.database.models import User, UserSettings


class AuthError(Exception):
    pass


class AuthService(AuthInterface):
    name = "auth"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {"module": self.name, "status": "ok"}

    async def register(self, email: str, password: str, display_name: str = "") -> dict:
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            raise AuthError("Email already registered")

        user = User(email=email, hashed_password=hash_password(password), display_name=display_name)
        self.db.add(user)
        await self.db.flush()

        self.db.add(UserSettings(user_id=user.id))
        await self.db.commit()
        await self.db.refresh(user)
        return {"id": str(user.id), "email": user.email, "display_name": user.display_name}

    async def authenticate(self, email: str, password: str) -> str:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthError("Invalid email or password")
        if not user.is_active:
            raise AuthError("User is inactive")

        return create_access_token(subject=str(user.id))

    async def get_user_from_token(self, token: str) -> dict:
        try:
            user_id = decode_access_token(token)
        except ValueError as exc:
            raise AuthError(str(exc)) from exc

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise AuthError("User not found")

        return {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "is_active": user.is_active,
        }
