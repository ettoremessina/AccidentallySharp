"""Tests for audio/midi.py — MIDI note number generation."""

import pytest
from theory.parser import parse_chord_name
from audio.midi import chord_to_midi_notes, _pitch_class_to_midi, _clamp_midi, MIDI_MIN, MIDI_MAX


def test_c4_midi():
    assert _pitch_class_to_midi(0, 4) == 60


def test_c3_midi():
    assert _pitch_class_to_midi(0, 3) == 48


def test_b3_midi():
    assert _pitch_class_to_midi(11, 3) == 59


def test_asharp3_midi():
    assert _pitch_class_to_midi(10, 3) == 58


def test_c_major_at_c3():
    chord = parse_chord_name("C")
    notes = chord_to_midi_notes(chord, root_octave=3)
    assert notes == [48, 52, 55]


def test_cmaj7_at_c3():
    chord = parse_chord_name("Cmaj7")
    notes = chord_to_midi_notes(chord, root_octave=3)
    assert notes == [48, 52, 55, 59]


def test_notes_are_sorted_ascending():
    chord = parse_chord_name("Cmaj7")
    notes = chord_to_midi_notes(chord)
    assert notes == sorted(notes)


@pytest.mark.parametrize("value, expected", [
    (20,  21),
    (21,  21),
    (60,  60),
    (108, 108),
    (109, 108),
])
def test_clamp_midi(value, expected):
    assert _clamp_midi(value) == expected


def test_no_note_below_midi_min():
    chord = parse_chord_name("C")
    notes = chord_to_midi_notes(chord, root_octave=-5)
    assert all(n >= MIDI_MIN for n in notes)


def test_no_note_above_midi_max():
    chord = parse_chord_name("B")
    notes = chord_to_midi_notes(chord, root_octave=9)
    assert all(n <= MIDI_MAX for n in notes)


def test_slash_chord_bass_is_lowest():
    chord = parse_chord_name("G/B")
    notes = chord_to_midi_notes(chord, root_octave=3)
    assert notes[0] < notes[1], "bass note must be lowest"
