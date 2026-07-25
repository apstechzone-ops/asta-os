from abc import abstractmethod

from backend.shared import ModuleBase


class AuthInterface(ModuleBase):
    """Contract for the Authentication module."""

    @abstractmethod
    async def register(self, email: str, password: str, display_name: str = "") -> dict:
        ...

    @abstractmethod
    async def authenticate(self, email: str, password: str) -> str:
        """Returns a signed access token on success, raises on failure."""
        ...

    @abstractmethod
    async def get_user_from_token(self, token: str) -> dict:
        ...
