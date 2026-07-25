import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database.models import UserSettings


def _client_config() -> dict:
    settings = get_settings()
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }


def build_auth_url(state: str) -> str:
    settings = get_settings()
    flow = Flow.from_client_config(
        _client_config(), scopes=settings.GOOGLE_SCOPES, redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent", state=state
    )
    return auth_url


def exchange_code_for_credentials(code: str) -> Credentials:
    settings = get_settings()
    flow = Flow.from_client_config(
        _client_config(), scopes=settings.GOOGLE_SCOPES, redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    flow.fetch_token(code=code)
    return flow.credentials


async def save_credentials(db: AsyncSession, user_id: str, credentials: Credentials) -> None:
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    settings_row = result.scalar_one_or_none()
    if settings_row is None:
        settings_row = UserSettings(user_id=user_id)
        db.add(settings_row)

    prefs = dict(settings_row.preferences or {})
    prefs["google_credentials"] = json.loads(credentials.to_json())
    settings_row.preferences = prefs
    await db.commit()


async def load_credentials(db: AsyncSession, user_id: str) -> Credentials | None:
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    settings_row = result.scalar_one_or_none()
    if settings_row is None or "google_credentials" not in (settings_row.preferences or {}):
        return None

    return Credentials.from_authorized_user_info(settings_row.preferences["google_credentials"])
