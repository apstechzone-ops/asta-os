from typing import Any

from backend.agents.interface import AgentInterface, AgentManagerInterface


class AgentManager(AgentManagerInterface):
    name = "agent_manager"

    def __init__(self) -> None:
        self._agents: dict[str, AgentInterface] = {}

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        self._agents.clear()

    def health(self) -> dict:
        return {"module": self.name, "status": "ok", "registered": list(self._agents.keys())}

    async def register_agent(self, agent: AgentInterface) -> None:
        self._agents[agent.name] = agent

    def list_agents(self) -> list[str]:
        return list(self._agents.keys())

    async def dispatch(self, task: dict) -> dict[str, Any]:
        for agent in self._agents.values():
            if await agent.can_handle(task):
                return await agent.execute(task)
        raise ValueError(f"No registered agent can handle task: {task}")


_agent_manager_singleton: AgentManager | None = None


def get_agent_manager() -> AgentManager:
    global _agent_manager_singleton
    if _agent_manager_singleton is None:
        _agent_manager_singleton = AgentManager()
    return _agent_manager_singleton
