"""Tests for theory/intervals.py — chord to pitch class set computation."""

import pytest
from theory.parser import parse_chord_name
from theory.intervals import chord_to_pitch_classes


@pytest.mark.parametrize("chord_name, expected", [
    # Triads
    ("C",    {0, 4, 7}),
    ("Cm",   {0, 3, 7}),
    ("Cdim", {0, 3, 6}),
    ("Caug", {0, 4, 8}),
    # Seventh chords
    ("C7",    {0, 4, 7, 10}),
    ("Cmaj7", {0, 4, 7, 11}),
    ("Cm7",   {0, 3, 7, 10}),
    ("Cdim7", {0, 3, 6, 9}),
    ("Cm7b5", {0, 3, 6, 10}),
    # Sus chords
    ("Csus2", {0, 2, 7}),
    ("Csus4", {0, 5, 7}),
])
def test_pitch_classes(chord_name, expected):
    chord = parse_chord_name(chord_name)
    assert chord_to_pitch_classes(chord) == expected


def test_c7_sharp11():
    # C7#11 → dominant {0,4,7,10} + #11 (18%12=6) → {0,4,6,7,10}
    chord = parse_chord_name("C7#11")
    pcs = chord_to_pitch_classes(chord)
    assert 6 in pcs   # raised 11th
    assert 10 in pcs  # minor 7th (from dominant quality)


def test_c7_flat9():
    # C7b9 → {0,4,7,10} + b9 (13%12=1) → {0,1,4,7,10}
    chord = parse_chord_name("C7b9")
    pcs = chord_to_pitch_classes(chord)
    assert 1 in pcs


def test_fsharp_major_transposition():
    # F# major = {6, 10, 1}
    chord = parse_chord_name("F#")
    assert chord_to_pitch_classes(chord) == {6, 10, 1}


def test_bb_minor_transposition():
    # Bb minor = {10, 1, 5}
    chord = parse_chord_name("Bbm")
    assert chord_to_pitch_classes(chord) == {10, 1, 5}
