"""Tests for theory/parser.py — chord name parsing."""

import pytest
from theory.parser import parse_chord_name


# --- Standard triads ---
def test_parse_c_major():
    chord = parse_chord_name("C")
    assert chord.root.pitchClass == 0
    assert chord.root.spelling == "C"
    assert chord.quality == "major"
    assert chord.extensions == []
    assert chord.bassNote is None


def test_parse_a_minor():
    chord = parse_chord_name("Am")
    assert chord.root.pitchClass == 9
    assert chord.quality == "minor"


def test_parse_fsharp_major():
    chord = parse_chord_name("F#")
    assert chord.root.pitchClass == 6
    assert chord.root.spelling == "F#"
    assert chord.quality == "major"


def test_parse_bb_major():
    chord = parse_chord_name("Bb")
    assert chord.root.pitchClass == 10
    assert chord.root.spelling == "Bb"
    assert chord.quality == "major"


# --- Seventh chords: critical distinctions ---
def test_parse_c7_is_dominant_not_major7():
    chord = parse_chord_name("C7")
    assert chord.quality == "dominant"
    assert all(e.degree != 7 for e in chord.extensions), "dominant quality implies m7; no extension needed"


def test_parse_cmaj7():
    chord = parse_chord_name("Cmaj7")
    assert chord.quality == "major7"


def test_parse_cm7_major():
    chord = parse_chord_name("CM7")
    assert chord.quality == "major7"


def test_parse_cm7_minor():
    chord = parse_chord_name("Cm7")
    assert chord.quality == "minor7"


def test_parse_cdim7_is_diminished7_not_half_diminished():
    chord = parse_chord_name("Cdim7")
    assert chord.quality == "diminished7"


def test_parse_cm7b5_is_half_diminished():
    chord = parse_chord_name("Cm7b5")
    assert chord.quality == "half-diminished"


def test_parse_half_dim_symbol():
    chord = parse_chord_name("Cø")
    assert chord.quality == "half-diminished"


# --- Extended chords ---
def test_parse_c9_implies_seventh():
    chord = parse_chord_name("C9")
    assert chord.quality == "dominant"
    degrees = [e.degree for e in chord.extensions]
    assert 9 in degrees


def test_parse_cadd9_no_seventh():
    chord = parse_chord_name("Cadd9")
    assert chord.quality == "major"
    degrees = [e.degree for e in chord.extensions]
    assert 9 in degrees
    assert 7 not in degrees


def test_parse_c6():
    chord = parse_chord_name("C6")
    assert chord.quality == "major"
    degrees = [e.degree for e in chord.extensions]
    assert 6 in degrees


# --- Sus chords ---
def test_parse_csus_is_sus4():
    chord = parse_chord_name("Csus")
    assert chord.quality == "sus4"


def test_parse_csus2():
    chord = parse_chord_name("Csus2")
    assert chord.quality == "sus2"


def test_parse_csus4():
    chord = parse_chord_name("Csus4")
    assert chord.quality == "sus4"


# --- Slash chords ---
def test_parse_g_slash_b():
    chord = parse_chord_name("G/B")
    assert chord.root.pitchClass == 7
    assert chord.quality == "major"
    assert chord.bassNote is not None
    assert chord.bassNote.pitchClass == 11
    assert chord.bassNote.spelling == "B"


def test_parse_c_slash_e():
    chord = parse_chord_name("C/E")
    assert chord.bassNote is not None
    assert chord.bassNote.pitchClass == 4


# --- Enharmonic equivalence ---
def test_enharmonic_db_vs_csharp():
    db = parse_chord_name("Db")
    cs = parse_chord_name("C#")
    assert db.root.pitchClass == cs.root.pitchClass == 1
    assert db.root.spelling == "Db"
    assert cs.root.spelling == "C#"


# --- Invalid input ---
def test_empty_string_raises():
    with pytest.raises(ValueError):
        parse_chord_name("")


def test_invalid_root_raises():
    with pytest.raises(ValueError):
        parse_chord_name("H7")
