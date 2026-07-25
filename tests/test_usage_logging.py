from backend.ai_providers.usage import UsageLogEntry
from tests.test_ai_router import FakeProvider, make_router


async def test_chat_success_logs_correct_fields():
    collected: list[UsageLogEntry] = []

    async def on_log(entry: UsageLogEntry) -> None:
        collected.append(entry)

    provider = FakeProvider("primary")
    provider.cost_per_1k_input = 1.0
    provider.cost_per_1k_output = 2.0
    provider.retry_count = 3
    router = make_router(provider)

    result = await router.chat(
        [{"role": "user", "content": "x" * 40}],  # 40 chars -> 10 estimated tokens
        on_log=on_log,
        session_id="sess-1",
        user_id="user-1",
        task_type="coding",
    )

    assert result == "primary: response"
    assert len(collected) == 1
    entry = collected[0]
    assert entry.provider == "primary"
    assert entry.model == "fake-model"
    assert entry.status == "success"
    assert entry.latency_ms >= 0
    assert entry.prompt_tokens == 10
    assert entry.fallback_index == 0
    assert entry.retries_configured == 3
    assert entry.session_id == "sess-1"
    assert entry.user_id == "user-1"
    assert entry.task_type == "coding"
    assert entry.error is None
    # cost = (10/1000 * 1.0) + (completion_tokens/1000 * 2.0), completion_tokens > 0
    assert entry.estimated_cost_usd > 0


async def test_chat_failure_logs_error_and_fallback_index():
    collected: list[UsageLogEntry] = []

    async def on_log(entry: UsageLogEntry) -> None:
        collected.append(entry)

    router = make_router(FakeProvider("dead", fail=True), FakeProvider("backup"))

    result = await router.chat([{"role": "user", "content": "hi"}], on_log=on_log)

    assert result == "backup: response"
    assert len(collected) == 2  # one failed attempt logged, one success logged
    assert collected[0].provider == "dead"
    assert collected[0].status == "failed"
    assert collected[0].fallback_index == 0
    assert collected[0].error is not None
    assert collected[1].provider == "backup"
    assert collected[1].status == "success"
    assert collected[1].fallback_index == 1


async def test_stream_success_logs_accumulated_completion_tokens():
    collected: list[UsageLogEntry] = []

    async def on_log(entry: UsageLogEntry) -> None:
        collected.append(entry)

    router = make_router(FakeProvider("primary", chunks=["a" * 20, "b" * 20]))

    result = [chunk async for chunk in router.stream([{"role": "user", "content": "hi"}], on_log=on_log)]

    assert "".join(result) == "a" * 20 + "b" * 20
    assert len(collected) == 1
    assert collected[0].status == "success"
    assert collected[0].completion_tokens == 10  # 40 chars / 4


async def test_broken_log_callback_does_not_break_chat():
    """Critical: a bug in logging must never take down the actual chat request."""

    async def broken_on_log(entry: UsageLogEntry) -> None:
        raise RuntimeError("logging backend is down")

    router = make_router(FakeProvider("primary"))
    result = await router.chat([{"role": "user", "content": "hi"}], on_log=broken_on_log)
    assert result == "primary: response"  # succeeded despite the logger exploding


async def test_no_log_callback_is_a_no_op():
    router = make_router(FakeProvider("primary"))
    result = await router.chat([{"role": "user", "content": "hi"}])  # no on_log at all
    assert result == "primary: response"


async def test_cost_estimate_is_zero_for_free_providers():
    collected: list[UsageLogEntry] = []

    async def on_log(entry: UsageLogEntry) -> None:
        collected.append(entry)

    provider = FakeProvider("primary")  # cost_per_1k_input/output default to 0.0 via base class
    router = make_router(provider)

    await router.chat([{"role": "user", "content": "hi"}], on_log=on_log)
    assert collected[0].estimated_cost_usd == 0.0
