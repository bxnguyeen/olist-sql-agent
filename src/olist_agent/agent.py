import os

from dotenv import load_dotenv
from openai import OpenAI

from olist_agent.tools import TOOL_SPECS, call_tool

load_dotenv()

SYSTEM_PROMPT = (
    "You answer questions about the Olist e-commerce database (PostgreSQL) "
    "by querying it with the provided tools. "
    "Base your answer only on query results, and include the key numbers."
)
MAX_STEPS = 10


def ask(question: str) -> str:
    """Answer a question by letting the LLM call tools until it has an answer."""
    client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=os.environ["LLM_MODEL"], messages=messages, tools=TOOL_SPECS
        )
        message = response.choices[0].message
        if not message.tool_calls:
            return message.content

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
            print(f"[tool] {call.function.name} {call.function.arguments}")
            result = call_tool(call.function.name, call.function.arguments)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return "Stopped: step limit reached without an answer."
