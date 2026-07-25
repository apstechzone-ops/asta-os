import asyncio

from google.oauth2.credentials import Credentials

from backend.google_workspace.client_factory import build_gmail


class GmailService:
    def __init__(self, creds: Credentials) -> None:
        self.client = build_gmail(creds)

    async def list_messages(self, query: str = "", max_results: int = 10) -> list[dict]:
        def _list():
            resp = (
                self.client.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )
            return resp.get("messages", [])

        return await asyncio.get_event_loop().run_in_executor(None, _list)

    async def get_message(self, message_id: str) -> dict:
        def _get():
            return self.client.users().messages().get(userId="me", id=message_id).execute()

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def send_message(self, raw_message: str) -> dict:
        def _send():
            return self.client.users().messages().send(userId="me", body={"raw": raw_message}).execute()

        return await asyncio.get_event_loop().run_in_executor(None, _send)
