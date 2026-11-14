import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from olist_agent.tools import TOOL_SPECS, call_tool

load_dotenv()

PROMPTS_DIR = Path("prompts")
DEFAULT_PROMPT_VERSION = "v1"


def load_prompt(version: str) -> str:
    """Read one versioned system prompt, e.g. prompts/v1.txt."""
    return (PROMPTS_DIR / f"{version}.txt").read_text().strip()

MAX_STEPS = 10
@dataclass
class ToolCall:
    """One tool call made by the LLM, with the result it got back."""

    name: str
    arguments: str
    result: str


@dataclass
class AgentResult:
    """The answer to one question, plus the measurements the eval needs."""

    answer: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    llm_calls: int = 0
    total_tokens: int = 0
    seconds: float = 0.0


def ask(question: str, prompt_version: str = DEFAULT_PROMPT_VERSION) -> AgentResult:
    """Answer a question by letting the LLM call tools until it has an answer."""
    client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])
    messages = [
        {"role": "system", "content": load_prompt(prompt_version)},
        {"role": "user", "content": question},
    ]
    result = AgentResult(answer="Stopped: step limit reached without an answer.")
    started = time.perf_counter()

    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=os.environ["LLM_MODEL"], messages=messages, tools=TOOL_SPECS
        )
        result.llm_calls += 1
        result.total_tokens += response.usage.total_tokens
        message = response.choices[0].message
        if not message.tool_calls:
            result.answer = message.content
            break

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in message.tool_calls
                ],
            }
        )
        for call in message.tool_calls:
            output = call_tool(call.function.name, call.function.arguments)
            result.tool_calls.append(ToolCall(call.function.name, call.function.arguments, output))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": output})

    result.seconds = time.perf_counter() - started
    return result
