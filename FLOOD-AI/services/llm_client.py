"""
LLM client wrapper.
Wraps OpenAI-compatible API calls used by ReportAgent and CoordinatorAgent.
Handles retries, token limits, and response parsing.
"""
from openai import OpenAI
from config import settings
from typing import Optional
from loguru import logger


_client = OpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url
)


def ask(prompt: str, system: str = "", max_tokens: int = 1000) -> Optional[str]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = _client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return None


def ask_json(prompt: str, system: str = "", max_tokens: int = 1000) -> Optional[dict]:
    import json
    raw = ask(prompt, system=system, max_tokens=max_tokens)
    if not raw:
        return None
    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"LLM JSON parse failed: {e} | raw: {raw[:200]}")
        return None