import pytest

from backend.agents.interface import AgentInterface
from backend.agents.manager import AgentManager


class EchoAgent(AgentInterface):
    name = "echo_agent"

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def health(self) -> dict:
        return {}

    async def can_handle(self, task: dict) -> bool:
        return task.get("type") == "echo"

    async def execute(self, task: dict) -> dict:
        return {"echo": task.get("payload")}


@pytest.mark.asyncio
async def test_dispatch_routes_to_matching_agent():
    mgr = AgentManager()
    await mgr.register_agent(EchoAgent())
    result = await mgr.dispatch({"type": "echo", "payload": "hello"})
    assert result == {"echo": "hello"}


@pytest.mark.asyncio
async def test_dispatch_no_match_raises():
    mgr = AgentManager()
    await mgr.register_agent(EchoAgent())
    with pytest.raises(ValueError):
        await mgr.dispatch({"type": "unknown"})
