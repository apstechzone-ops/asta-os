import asyncio

from google.oauth2.credentials import Credentials

from backend.google_workspace.client_factory import build_drive


class DriveService:
    def __init__(self, creds: Credentials) -> None:
        self.client = build_drive(creds)

    async def list_files(self, query: str = "", page_size: int = 20) -> list[dict]:
        def _list():
            resp = (
                self.client.files()
                .list(q=query, pageSize=page_size, fields="files(id, name, mimeType, modifiedTime)")
                .execute()
            )
            return resp.get("files", [])

        return await asyncio.get_event_loop().run_in_executor(None, _list)

    async def get_file_metadata(self, file_id: str) -> dict:
        def _get():
            return self.client.files().get(fileId=file_id).execute()

        return await asyncio.get_event_loop().run_in_executor(None, _get)
