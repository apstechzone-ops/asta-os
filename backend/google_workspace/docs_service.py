import asyncio

from google.oauth2.credentials import Credentials

from backend.google_workspace.client_factory import build_docs


class DocsService:
    def __init__(self, creds: Credentials) -> None:
        self.client = build_docs(creds)

    async def create_document(self, title: str, content: str = "") -> dict:
        def _create():
            doc = self.client.documents().create(body={"title": title}).execute()
            if content:
                self.client.documents().batchUpdate(
                    documentId=doc["documentId"],
                    body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]},
                ).execute()
            return doc

        return await asyncio.get_event_loop().run_in_executor(None, _create)

    async def get_document(self, document_id: str) -> dict:
        def _get():
            return self.client.documents().get(documentId=document_id).execute()

        return await asyncio.get_event_loop().run_in_executor(None, _get)
