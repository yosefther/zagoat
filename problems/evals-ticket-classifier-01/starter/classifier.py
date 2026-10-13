from openai import OpenAI

from prompts import build_prompt

MODEL = "gpt-4o-mini"


def classify(client: OpenAI, ticket: str) -> str:
    """Ask the model for a label. Returns the raw reply; models don't always follow the format."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": build_prompt(ticket)}],
        temperature=0,
    )
    return response.choices[0].message.content or ""
