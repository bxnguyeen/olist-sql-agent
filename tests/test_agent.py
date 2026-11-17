from types import SimpleNamespace

from olist_agent import agent
from olist_agent.agent import AgentResult, ToolCall, ask
from olist_agent.evaluate import last_successful_sql


def fake_response(content=None, tool_calls=None, tokens=10):
    """Build an object shaped like an OpenAI chat completion response."""
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
        usage=SimpleNamespace(total_tokens=tokens),
    )


def fake_tool_call(name, arguments):
    """Build an object shaped like one tool call requested by the LLM."""
    return SimpleNamespace(id="call_1", function=SimpleNamespace(name=name, arguments=arguments))


class FakeClient:
    """Stands in for OpenAI(): returns scripted responses instead of calling an API."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        return self.responses.pop(0)


def use_fake_llm(monkeypatch, responses):
    """Make ask() talk to FakeClient and a fake tool instead of Groq and the database."""
    monkeypatch.setenv("LLM_BASE_URL", "http://fake")
    monkeypatch.setenv("LLM_API_KEY", "fake")
    monkeypatch.setenv("LLM_MODEL", "fake-model")
    monkeypatch.setattr(agent, "OpenAI", lambda **kwargs: FakeClient(responses))
    monkeypatch.setattr(agent, "call_tool", lambda name, arguments: "count\n42")


def test_ask_runs_tool_then_answers(monkeypatch):
    sql_call = fake_tool_call("run_sql", '{"query": "SELECT count(*) FROM t"}')
    use_fake_llm(
        monkeypatch,
        [
            fake_response(tool_calls=[sql_call]),
            fake_response(content="There are 42 orders."),
        ],
    )
    result = ask("How many orders?")
    assert result.answer == "There are 42 orders."
    assert result.llm_calls == 2
    assert result.total_tokens == 20
    assert result.tool_calls == [
        ToolCall("run_sql", '{"query": "SELECT count(*) FROM t"}', "count\n42")
    ]


def test_ask_stops_at_step_limit(monkeypatch):
    list_call = fake_tool_call("list_tables", "{}")
    use_fake_llm(monkeypatch, [fake_response(tool_calls=[list_call])] * agent.MAX_STEPS)
    result = ask("A question the LLM never finishes")
    assert result.answer.startswith("Stopped")
    assert result.llm_calls == agent.MAX_STEPS


def test_last_successful_sql_skips_failed_queries():
    result = AgentResult(
        answer="",
        tool_calls=[
            ToolCall("run_sql", '{"query": "SELECT 1"}', "?column?\n1"),
            ToolCall(
                "run_sql",
                '{"query": "SELECT oops"}',
                "SQL error: column does not exist",
            ),
        ],
    )
    assert last_successful_sql(result) == "SELECT 1"


def test_last_successful_sql_without_queries_is_none():
    result = AgentResult(answer="", tool_calls=[ToolCall("list_tables", "{}", "...")])
    assert last_successful_sql(result) is None
