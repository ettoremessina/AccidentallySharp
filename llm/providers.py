"""LLM provider implementations for chord suggestions."""

import abc
import json
import re

MAX_TOKENS = 512

SYSTEM_PROMPT = """\
You are a music theory assistant helping a beginner explore chord progressions.
Given a harmonic context, suggest the next chord to play.

Respond ONLY with a JSON object in this exact format:
{
  "suggestions": [
    {"chord": "<chord name>", "degree": <integer>, "reason": "<plain English reason>"},
    ...
  ]
}

Rules:
- Suggest exactly 3 chords.
- Prefer diatonic chords in the declared key.
- Keep reasons short (one sentence) and beginner-friendly.
- chord must be a standard chord name (e.g. "Am", "G7", "F").
- degree must be an integer (1-7).
"""

def _parse_json(raw: str) -> dict:
    """
    Extract and parse a JSON object from an LLM response.

    Handles:
    - Pure JSON
    - Markdown code fences (```json ... ``` or ``` ... ```)
    - JSON embedded in surrounding prose (searches for first { ... last })

    Raises ValueError with the raw response snippet on failure.
    """
    text = raw.strip()

    # Strip markdown code fences
    text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract the first {...} block
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    snippet = raw[:300].replace('\n', '↵')
    raise ValueError(
        f"Model did not return valid JSON.\n"
        f"Response was: {snippet!r}"
    )


PROGRESSION_SYSTEM_PROMPT = """\
You are a music theory assistant helping a beginner explore chord progressions.
Generate a chord progression based on the given key, style, and requested length.

Respond ONLY with a JSON object in this exact format:
{
  "progression": ["C", "Am", "F", "G"]
}

Rules:
- Return exactly the number of chords specified by the "count" field in the request.
- Prefer simple, recognizable chords suitable for beginners.
- Stay mostly diatonic to the key; use colour chords only when the style calls for it.
- Chord names must be standard notation (e.g. "Am", "G7", "Cmaj7", "F").
"""


class LLMProvider(abc.ABC):
    """Abstract base for all LLM providers."""

    @abc.abstractmethod
    def get_suggestions(self, context: dict) -> list[dict]:
        """Return a list of suggestion dicts. Raises on failure."""

    @abc.abstractmethod
    def get_progression(self, key_root: str, key_mode: str, style_hint: str, count: int = 4) -> list[str]:
        """Return a list of chord name strings for a full progression. Raises on failure."""


class _OpenAICompatibleProvider(LLMProvider):
    """Shared logic for OpenAI-compatible endpoints (OpenAI, Ollama, LMStudio)."""

    def __init__(self, client, model: str) -> None:
        self._client = client
        self._model = model

    def get_suggestions(self, context: dict) -> list[dict]:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
        )
        raw = response.choices[0].message.content.strip()
        data = _parse_json(raw)
        return data.get("suggestions", [])

    def get_progression(self, key_root: str, key_mode: str, style_hint: str, count: int = 4) -> list[str]:
        context = {
            "key": {"root": key_root, "mode": key_mode},
            "styleHint": style_hint,
            "count": count,
        }
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": PROGRESSION_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
        )
        raw = response.choices[0].message.content.strip()
        data = _parse_json(raw)
        return data.get("progression", [])


class OpenAIProvider(_OpenAICompatibleProvider):
    """OpenAI API (requires OPENAI_API_KEY env var)."""

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        import openai
        super().__init__(openai.OpenAI(), model)


class OllamaProvider(_OpenAICompatibleProvider):
    """Ollama local server (OpenAI-compatible at localhost:11434)."""

    DEFAULT_MODEL = "llama3"
    DEFAULT_URL = "http://localhost:11434/v1"

    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_URL) -> None:
        import openai
        super().__init__(openai.OpenAI(base_url=base_url, api_key="ollama"), model)


class LMStudioProvider(_OpenAICompatibleProvider):
    """LM Studio local server (OpenAI-compatible at localhost:1234)."""

    DEFAULT_MODEL = "local-model"
    DEFAULT_URL = "http://localhost:1234/v1"

    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_URL) -> None:
        import openai
        super().__init__(openai.OpenAI(base_url=base_url, api_key="lm-studio"), model)


class AnthropicProvider(LLMProvider):
    """Anthropic API (requires ANTHROPIC_API_KEY env var)."""

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        import anthropic
        self._client = anthropic.Anthropic()
        self._model = model

    def get_suggestions(self, context: dict) -> list[dict]:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
        )
        raw = message.content[0].text.strip()
        data = _parse_json(raw)
        return data.get("suggestions", [])

    def get_progression(self, key_root: str, key_mode: str, style_hint: str, count: int = 4) -> list[str]:
        context = {
            "key": {"root": key_root, "mode": key_mode},
            "styleHint": style_hint,
            "count": count,
        }
        message = self._client.messages.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            system=PROGRESSION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
        )
        raw = message.content[0].text.strip()
        data = _parse_json(raw)
        return data.get("progression", [])


# Registry: name → provider class
PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai":    OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama":    OllamaProvider,
    "lmstudio":  LMStudioProvider,
}
