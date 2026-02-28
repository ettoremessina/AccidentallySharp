"""Validate LLM chord suggestions before showing them to the user."""

from theory.enharmonic import spelling_to_pitch_class

# Diatonic pitch classes for each degree in major and natural/harmonic minor
_MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
_MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]  # natural minor

# Diatonic chord qualities per degree in major (1-indexed)
_MAJOR_DIATONIC_QUALITY: dict[int, str] = {
    1: "major", 2: "minor", 3: "minor", 4: "major",
    5: "major", 6: "minor", 7: "diminished",
}

# Diatonic chord qualities per degree in minor (harmonic)
_MINOR_DIATONIC_QUALITY: dict[int, str] = {
    1: "minor", 2: "diminished", 3: "major", 4: "minor",
    5: "major", 6: "major", 7: "diminished",
}

BORROWED_LABEL = "borrowed chord"


def _key_pitch_classes(key_root: str, key_mode: str) -> set[int]:
    """Return the set of pitch classes in the given key."""
    root_pc = spelling_to_pitch_class(key_root)
    intervals = _MAJOR_SCALE_INTERVALS if key_mode == "major" else _MINOR_SCALE_INTERVALS
    return {(root_pc + i) % 12 for i in intervals}


def _is_diatonic(suggestion_pc: int, key_root: str, key_mode: str) -> bool:
    return suggestion_pc in _key_pitch_classes(key_root, key_mode)


def _is_borrowed(suggestion_pc: int, key_root: str, key_mode: str) -> bool:
    """Check for commonly accepted borrowed chords."""
    root_pc = spelling_to_pitch_class(key_root)
    if key_mode == "major":
        # bVII: one semitone below the leading tone
        bvii_pc = (root_pc + 10) % 12
        return suggestion_pc == bvii_pc
    else:
        # major IV in minor: degree 4 with major quality (same pitch class)
        iv_pc = (root_pc + 5) % 12
        return suggestion_pc == iv_pc


def validate_suggestion(
    suggestion: dict,
    current_chord_spelling: str,
    key_root: str,
    key_mode: str,
) -> tuple[bool, str]:
    """
    Validate a single LLM suggestion dict.

    Returns:
        (is_valid, label) where label is "" for diatonic,
        BORROWED_LABEL for borrowed, and "" when invalid.
    """
    chord_str = suggestion.get("chord")
    if not chord_str or not isinstance(chord_str, str):
        return False, ""

    # Reject same as current chord
    try:
        current_pc = spelling_to_pitch_class(current_chord_spelling)
        suggestion_root = chord_str.strip()[:2] if len(chord_str) > 1 else chord_str.strip()
        # Extract just the root spelling
        root_part = ""
        for length in (2, 1):
            candidate = chord_str[:length]
            try:
                spelling_to_pitch_class(candidate)
                root_part = candidate
                break
            except ValueError:
                continue
        if not root_part:
            return False, ""
        suggestion_pc = spelling_to_pitch_class(root_part)
    except ValueError:
        return False, ""

    if suggestion_pc == current_pc:
        return False, ""

    if _is_diatonic(suggestion_pc, key_root, key_mode):
        return True, ""

    if _is_borrowed(suggestion_pc, key_root, key_mode):
        return True, BORROWED_LABEL

    return False, ""
