import asyncio
import datetime

from google.oauth2.credentials import Credentials

from backend.google_workspace.client_factory import build_calendar


class CalendarService:
    def __init__(self, creds: Credentials) -> None:
        self.client = build_calendar(creds)

    async def list_upcoming_events(self, max_results: int = 10) -> list[dict]:
        def _list():
            now = datetime.datetime.utcnow().isoformat() + "Z"
            resp = (
                self.client.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return resp.get("items", [])

        return await asyncio.get_event_loop().run_in_executor(None, _list)

    async def create_event(self, event: dict) -> dict:
        def _create():
            return self.client.events().insert(calendarId="primary", body=event).execute()

        return await asyncio.get_event_loop().run_in_executor(None, _create)
