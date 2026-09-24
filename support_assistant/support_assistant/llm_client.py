"""
Thin wrapper around a real LLM call, used ONLY by the optional MOCK_LLM=0
extension. Never imported or invoked when MOCK_LLM is left at its default,
so the graded baseline has no dependency on this file, no API key, and no
network access requirement.

Defaults to Groq's free-tier API (console.groq.com) since it requires only
a free account signup and no payment. Swap the base_url/model/env var names
for any other genuinely-free-tier LLM API if Groq is unavailable to you.
"""

import os

from groq import Groq  # pip install groq  (only needed for MOCK_LLM=0)

_client: "Groq | None" = None


def _get_client() -> "Groq":
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "MOCK_LLM=0 requires GROQ_API_KEY to be set (Groq free tier, "
                "console.groq.com). Never hardcode the key in source."
            )
        _client = Groq(api_key=api_key)
    return _client


def call_llm(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    """Send a single-turn prompt to the LLM and return its text response."""
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=200,
    )
    return response.choices[0].message.content or ""
