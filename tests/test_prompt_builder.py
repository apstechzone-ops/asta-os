from backend.planner.prompt_builder import PromptBuilder


class FakeMemory:
    def __init__(self, search_results=None, raise_on_search=False):
        self._results = search_results or []
        self._raise = raise_on_search

    async def search_vector(self, query, top_k=5, filters=None):
        if self._raise:
            raise ConnectionError("chroma unreachable")
        return self._results

    async def add_short_term(self, *a, **k): pass
    async def get_recent_messages(self, *a, **k): return []
    async def add_long_term(self, *a, **k): return "x"
    async def list_sessions(self, *a, **k): return []
    async def search_structured(self, *a, **k): return []
    async def summarize_session(self, *a, **k): return ""
    async def startup(self): pass
    async def shutdown(self): pass
    def health(self): return {}


class FakeRAG:
    def __init__(self, retrieve_results=None, raise_on_retrieve=False):
        self._results = retrieve_results or []
        self._raise = raise_on_retrieve

    async def retrieve(self, query, top_k=5):
        if self._raise:
            raise ConnectionError("chroma unreachable")
        return self._results

    async def ingest_document(self, *a, **k): return "doc-1"
    async def delete_document(self, *a, **k): pass
    async def startup(self): pass
    async def shutdown(self): pass
    def health(self): return {}


async def test_build_includes_memory_context_when_available():
    memory = FakeMemory(search_results=[{"content": "User prefers dark mode", "metadata": {}, "id": "1", "score": 0.9}])
    builder = PromptBuilder(memory=memory, rag=None)

    messages = await builder.build(
        system_prompt="You are Asta",
        user_id="user-1",
        message="what theme should I use",
        history=[],
    )

    user_content = messages[1]["content"]
    assert "Relevant memories about this user" in user_content
    assert "User prefers dark mode" in user_content


async def test_build_includes_rag_context_when_available():
    memory = FakeMemory(search_results=[])
    rag = FakeRAG(retrieve_results=[{"content": "The API rate limit is 100/min", "metadata": {}, "id": "1", "score": 0.8}])
    builder = PromptBuilder(memory=memory, rag=rag)

    messages = await builder.build(
        system_prompt="You are Asta",
        user_id="user-1",
        message="what's the rate limit",
        history=[],
    )

    user_content = messages[1]["content"]
    assert "Relevant knowledge base context" in user_content
    assert "rate limit is 100/min" in user_content


async def test_build_degrades_gracefully_when_memory_search_fails():
    memory = FakeMemory(raise_on_search=True)
    builder = PromptBuilder(memory=memory, rag=None)

    messages = await builder.build(
        system_prompt="You are Asta", user_id="user-1", message="hello", history=[]
    )

    # Should not raise, and should simply omit the memories block
    assert "Relevant memories" not in messages[1]["content"]
    assert "User: hello" in messages[1]["content"]


async def test_build_degrades_gracefully_when_rag_fails():
    memory = FakeMemory()
    rag = FakeRAG(raise_on_retrieve=True)
    builder = PromptBuilder(memory=memory, rag=rag)

    messages = await builder.build(
        system_prompt="You are Asta", user_id="user-1", message="hello", history=[]
    )

    assert "Relevant knowledge base" not in messages[1]["content"]


async def test_build_works_with_no_rag_configured():
    memory = FakeMemory()
    builder = PromptBuilder(memory=memory, rag=None)

    messages = await builder.build(
        system_prompt="You are Asta", user_id="user-1", message="hello", history=[]
    )

    assert messages[0] == {"role": "system", "content": "You are Asta"}
    assert "User: hello" in messages[1]["content"]


async def test_build_includes_tool_context_when_present():
    memory = FakeMemory()
    builder = PromptBuilder(memory=memory, rag=None)

    messages = await builder.build(
        system_prompt="You are Asta",
        user_id="user-1",
        message="what's the weather",
        history=[],
        tool_context="Tool `weather` returned: 72F and sunny",
    )

    assert "72F and sunny" in messages[1]["content"]


def test_format_history_empty():
    assert PromptBuilder.format_history([]) == "(no prior messages)"


def test_format_history_formats_role_and_content():
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    result = PromptBuilder.format_history(history)
    assert result == "user: hi\nassistant: hello"


def test_format_history_respects_limit():
    history = [{"role": "user", "content": str(i)} for i in range(20)]
    result = PromptBuilder.format_history(history, limit=5)
    assert result.count("\n") == 4  # 5 lines = 4 newlines
    assert "19" in result  # most recent kept
    assert "0" not in result.split("\n")[0]  # oldest dropped
