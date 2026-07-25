from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build


def build_gmail(creds: Credentials) -> Resource:
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def build_drive(creds: Credentials) -> Resource:
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def build_calendar(creds: Credentials) -> Resource:
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def build_docs(creds: Credentials) -> Resource:
    return build("docs", "v1", credentials=creds, cache_discovery=False)
