from backend.memory.conversation_manager import ConversationManager


class FakeMemory:
    def __init__(self, messages=None, summary="a summary of the conversation"):
        self._messages = messages or []
        self._summary = summary
        self.saved = []

    async def add_short_term(self, session_id, role, content, user_id=None):
        self.saved.append((session_id, role, content, user_id))

    async def get_recent_messages(self, session_id, limit=20):
        return self._messages[-limit:]

    async def summarize_session(self, session_id):
        return self._summary

    async def add_long_term(self, *a, **k): return "x"
    async def search_vector(self, *a, **k): return []
    async def search_structured(self, *a, **k): return []
    async def list_sessions(self, *a, **k): return []
    async def startup(self): pass
    async def shutdown(self): pass
    def health(self): return {}


async def test_save_message_delegates_to_memory():
    memory = FakeMemory()
    cm = ConversationManager(memory=memory)
    await cm.save_message("session-1", "user", "hello", user_id="u1")
    assert memory.saved == [("session-1", "user", "hello", "u1")]


async def test_load_history_delegates_to_memory():
    memory = FakeMemory(messages=[{"role": "user", "content": "hi"}])
    cm = ConversationManager(memory=memory)
    result = await cm.load_history("session-1", limit=5)
    assert result == [{"role": "user", "content": "hi"}]


async def test_summarize_delegates_to_memory():
    memory = FakeMemory(summary="the user asked about pricing")
    cm = ConversationManager(memory=memory)
    assert await cm.summarize("session-1") == "the user asked about pricing"


async def test_trim_history_returns_unchanged_when_under_budget():
    messages = [{"role": "user", "content": "short"} for _ in range(3)]
    memory = FakeMemory(messages=messages)
    cm = ConversationManager(memory=memory, max_history_chars=4000)

    result = await cm.trim_history("session-1")
    assert result == messages  # untouched — well under budget


async def test_trim_history_falls_back_to_summary_when_over_budget():
    # 20 messages of 500 chars each = 10,000 chars, well over a 4000 budget
    messages = [{"role": "user", "content": "x" * 500} for _ in range(20)]
    memory = FakeMemory(messages=messages, summary="SUMMARY_MARKER")
    cm = ConversationManager(memory=memory, max_history_chars=4000, keep_recent=4)

    result = await cm.trim_history("session-1", limit=50)

    assert result[0]["content"] == "[Earlier conversation summary]: SUMMARY_MARKER"
    assert len(result) == 1 + 4
    assert result[1:] == messages[-4:]


async def test_trim_history_skips_summary_line_if_summary_is_empty():
    messages = [{"role": "user", "content": "x" * 500} for _ in range(20)]
    memory = FakeMemory(messages=messages, summary="")
    cm = ConversationManager(memory=memory, max_history_chars=4000, keep_recent=4)

    result = await cm.trim_history("session-1", limit=50)

    assert len(result) == 4
    assert result == messages[-4:]


async def test_trim_history_does_not_trim_short_message_lists_even_if_verbose():
    messages = [{"role": "user", "content": "x" * 5000}]
    memory = FakeMemory(messages=messages)
    cm = ConversationManager(memory=memory, max_history_chars=100, keep_recent=4)

    result = await cm.trim_history("session-1")
    assert result == messages
