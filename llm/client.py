"""LLM client — thin dispatcher that delegates to the active provider."""

from llm.providers import LLMProvider, PROVIDERS, OpenAIProvider

_active_provider: LLMProvider | None = None


def configure(provider_name: str = "openai", **kwargs) -> None:
    """
    Select and initialise the LLM provider.

    Args:
        provider_name: One of "openai", "anthropic", "ollama", "lmstudio".
        **kwargs: Passed to the provider constructor.
                  Useful kwargs per provider:
                  - openai/anthropic:  model="gpt-4o-mini" / model="claude-sonnet-4-6"
                  - ollama:            model="llama3", base_url="http://localhost:11434/v1"
                  - lmstudio:          model="local-model", base_url="http://localhost:1234/v1"

    Raises:
        ValueError: if provider_name is not recognised.
    """
    global _active_provider
    cls = PROVIDERS.get(provider_name)
    if cls is None:
        raise ValueError(
            f"Unknown provider {provider_name!r}. "
            f"Valid choices: {list(PROVIDERS)}"
        )
    _active_provider = cls(**kwargs)


def _ensure_provider() -> LLMProvider:
    global _active_provider
    if _active_provider is None:
        configure()
    return _active_provider  # type: ignore[return-value]


def get_chord_suggestions(context: dict) -> list[dict]:
    """
    Call the active LLM provider with a harmonic context.

    Returns a list of {"chord": str, "degree": int, "reason": str} dicts.
    Raises on network/API/parse failure — callers should catch and display the error.
    """
    return _ensure_provider().get_suggestions(context)


def get_chord_progression(key_root: str, key_mode: str, style_hint: str, count: int = 4) -> list[str]:
    """
    Ask the active LLM provider to generate a full chord progression.

    Returns a list of chord name strings (e.g. ["C", "Am", "F", "G"]).
    Raises on network/API/parse failure — callers should catch and display the error.
    """
    return _ensure_provider().get_progression(key_root, key_mode, style_hint, count)
