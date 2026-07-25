import pytest

from backend.tools.manager import ToolManager


@pytest.mark.asyncio
async def test_register_and_execute_tool():
    tm = ToolManager()

    async def add(a: int, b: int) -> int:
        return a + b

    await tm.register("add", "Adds two numbers", {"a": "int", "b": "int"}, add)
    result = await tm.execute("add", {"a": 2, "b": 3})
    assert result == 5


@pytest.mark.asyncio
async def test_describe_tools_lists_registered():
    tm = ToolManager()
    await tm.register("noop", "does nothing", {}, lambda: None)
    descriptions = tm.describe_tools()
    assert descriptions == [{"name": "noop", "description": "does nothing", "parameters": {}}]


@pytest.mark.asyncio
async def test_execute_unknown_tool_raises():
    tm = ToolManager()
    with pytest.raises(ValueError):
        await tm.execute("missing", {})
