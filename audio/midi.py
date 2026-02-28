"""Convert chord internal representation to MIDI note numbers."""

from theory.chord import Chord
from theory.intervals import QUALITY_INTERVALS, EXTENSION_NATURAL_OFFSET

MIDI_MIN = 21   # A0
MIDI_MAX = 108  # C8
DEFAULT_OCTAVE = 3  # Root placed at octave 3 (C3 = MIDI 48)


def _pitch_class_to_midi(pitch_class: int, octave: int) -> int:
    """Convert a pitch class and octave to a MIDI note number."""
    return (octave + 1) * 12 + pitch_class


def _clamp_midi(note: int) -> int:
    """Clamp a MIDI note to the piano range [21, 108]."""
    return max(MIDI_MIN, min(MIDI_MAX, note))


def chord_to_midi_notes(chord: Chord, root_octave: int = DEFAULT_OCTAVE) -> list[int]:
    """
    Convert a Chord to an ascending list of clamped MIDI note numbers.

    Uses close voicing: root at root_octave, remaining notes stacked upward
    within the smallest possible interval above the previous note.

    Args:
        chord: Internal chord representation.
        root_octave: Octave for the root note (default 3, i.e. C3 = MIDI 48).

    Returns:
        Sorted list of MIDI note numbers (ascending), clamped to [21, 108].
    """
    root_pc = chord.root.pitchClass

    # Collect semitone offsets from root
    base_offsets = list(QUALITY_INTERVALS.get(chord.quality, []))

    for ext in chord.extensions:
        natural = EXTENSION_NATURAL_OFFSET.get(ext.degree, 0)
        offset = natural + ext.alteration
        base_offsets.append(offset)

    # Deduplicate by offset value, keep sorted
    base_offsets = sorted(set(base_offsets))

    # Build MIDI notes using close voicing
    root_midi = _pitch_class_to_midi(root_pc, root_octave)
    notes: list[int] = [root_midi]

    for offset in base_offsets[1:]:
        pc = (root_pc + offset) % 12
        # Adjust offset to be the actual semitones above root
        # We want close voicing: smallest positive interval above previous note
        candidate = root_midi + offset
        while candidate <= notes[-1]:
            candidate += 12
        notes.append(candidate)

    # Handle slash chord bass note (place one octave below root)
    result = notes
    if chord.bassNote is not None:
        bass_midi = _pitch_class_to_midi(chord.bassNote.pitchClass, root_octave - 1)
        result = [bass_midi] + notes

    return [_clamp_midi(n) for n in result]
