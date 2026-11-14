import sys

from olist_agent.agent import ask


def main() -> None:
    """Command-line entry point: olist-ask "your question"."""
    if len(sys.argv) < 2:
        print('Usage: olist-ask "your question"')
        sys.exit(1)
    result = ask(" ".join(sys.argv[1:]))
    for call in result.tool_calls:
        print(f"[tool] {call.name} {call.arguments}")
    print(result.answer)
    print(f"({result.llm_calls} LLM calls, {result.total_tokens} tokens, {result.seconds:.1f}s)")
