"""Interval computation: chord internal representation → set of pitch classes."""

from theory.chord import Chord

# Semitone offsets from root for each base quality
QUALITY_INTERVALS: dict[str, list[int]] = {
    "major":          [0, 4, 7],
    "minor":          [0, 3, 7],
    "dominant":       [0, 4, 7, 10],
    "major7":         [0, 4, 7, 11],
    "minor7":         [0, 3, 7, 10],
    "diminished":     [0, 3, 6],
    "diminished7":    [0, 3, 6, 9],
    "half-diminished":[0, 3, 6, 10],
    "augmented":      [0, 4, 8],
    "sus2":           [0, 2, 7],
    "sus4":           [0, 5, 7],
}

# Natural semitone offset from root for each extension degree (before alteration)
EXTENSION_NATURAL_OFFSET: dict[int, int] = {
    2:  2,
    4:  5,
    5:  7,
    6:  9,
    7:  11,
    9:  14,
    11: 17,
    13: 21,
}


def chord_to_pitch_classes(chord: Chord) -> set[int]:
    """Return the set of pitch classes (0–11) for all notes in the chord."""
    root_pc = chord.root.pitchClass
    base = QUALITY_INTERVALS.get(chord.quality, [])
    pitch_classes: set[int] = {(root_pc + interval) % 12 for interval in base}

    for ext in chord.extensions:
        natural = EXTENSION_NATURAL_OFFSET.get(ext.degree, 0)
        offset = natural + ext.alteration
        pitch_classes.add((root_pc + offset) % 12)

    return pitch_classes
