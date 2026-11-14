import sys

from olist_agent.agent import ask


def main() -> None:
    """Command-line entry point: olist-ask "your question"."""
    if len(sys.argv) < 2:
        print('Usage: olist-ask "your question"')
        sys.exit(1)
    print(ask(" ".join(sys.argv[1:])))
