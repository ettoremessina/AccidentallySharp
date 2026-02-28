"""Build the harmonic context dict to send to the LLM."""

from theory.chord import Chord

MAX_PROGRESSION_HISTORY = 4


def build_harmonic_context(
    key_root: str,
    key_mode: str,
    progression: list[dict],
    current_chord: Chord,
    current_degree: int,
    style_hint: str = "pop",
) -> dict:
    """
    Build the context object sent to the LLM.

    Args:
        key_root: Root note of the key, e.g. "C".
        key_mode: "major" or "minor".
        progression: List of {"degree": int, "chord": str} dicts (full history).
        current_chord: The chord currently being played.
        current_degree: Scale degree of current_chord.
        style_hint: Genre hint, e.g. "pop", "jazz", "blues".

    Returns:
        A dict ready to be serialised to JSON and sent to the LLM.
    """
    recent = progression[-MAX_PROGRESSION_HISTORY:]
    return {
        "key": {"root": key_root, "mode": key_mode},
        "progression": recent,
        "currentChord": {
            "degree": current_degree,
            "chord": current_chord.root.spelling,
        },
        "styleHint": style_hint,
    }
