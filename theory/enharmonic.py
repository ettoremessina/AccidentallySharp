"""Enharmonic spelling utilities."""

# Maps note spellings to their pitchClass (0–11)
SPELLING_TO_PITCH_CLASS: dict[str, int] = {
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11,
}

# Preferred display spellings (sharp vs flat preference follows common practice)
PREFERRED_SPELLINGS: dict[int, str] = {
    0: "C", 1: "C#", 2: "D", 3: "Eb", 4: "E",
    5: "F", 6: "F#", 7: "G", 8: "Ab", 9: "A",
    10: "Bb", 11: "B",
}


def spelling_to_pitch_class(spelling: str) -> int:
    """Convert a note spelling to its pitchClass (0–11)."""
    result = SPELLING_TO_PITCH_CLASS.get(spelling)
    if result is None:
        raise ValueError(f"Unknown note spelling: {spelling!r}")
    return result


def pitch_class_to_preferred_spelling(pitch_class: int) -> str:
    """Return the preferred display spelling for a pitchClass."""
    if not (0 <= pitch_class <= 11):
        raise ValueError(f"pitchClass must be 0–11, got {pitch_class}")
    return PREFERRED_SPELLINGS[pitch_class]


def are_enharmonic(spelling_a: str, spelling_b: str) -> bool:
    """Return True if two spellings refer to the same pitch class."""
    return spelling_to_pitch_class(spelling_a) == spelling_to_pitch_class(spelling_b)
