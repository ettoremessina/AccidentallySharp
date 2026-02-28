"""Tests for llm/validator.py — LLM suggestion validation."""

import pytest
from llm.validator import validate_suggestion, BORROWED_LABEL


def _make(chord: str, degree: int = 1, reason: str = "") -> dict:
    return {"chord": chord, "degree": degree, "reason": reason}


# --- Diatonic — must pass ---
def test_g_is_diatonic_in_c_major():
    valid, label = validate_suggestion(_make("G"), "F", "C", "major")
    assert valid is True
    assert label == ""


def test_am_is_diatonic_in_c_major():
    valid, label = validate_suggestion(_make("Am"), "F", "C", "major")
    assert valid is True


def test_bdim_is_diatonic_in_c_major():
    valid, label = validate_suggestion(_make("Bdim"), "G", "C", "major")
    assert valid is True


# --- Borrowed — must pass with label ---
def test_bb_is_borrowed_in_c_major():
    valid, label = validate_suggestion(_make("Bb"), "G", "C", "major")
    assert valid is True
    assert label == BORROWED_LABEL


# --- Out of key — must be rejected ---
def test_csharp_rejected_in_c_major():
    valid, _ = validate_suggestion(_make("C#"), "G", "C", "major")
    assert valid is False


def test_eb_rejected_in_g_major():
    valid, _ = validate_suggestion(_make("Eb"), "D", "G", "major")
    assert valid is False


# --- Same as current chord — must be rejected ---
def test_same_as_current_chord_rejected():
    valid, _ = validate_suggestion(_make("G"), "G", "C", "major")
    assert valid is False


# --- Malformed input — must not crash ---
def test_missing_chord_field():
    valid, _ = validate_suggestion({"degree": 1, "reason": "x"}, "G", "C", "major")
    assert valid is False


def test_chord_is_none():
    valid, _ = validate_suggestion({"chord": None, "degree": 1}, "G", "C", "major")
    assert valid is False


def test_empty_dict():
    valid, _ = validate_suggestion({}, "G", "C", "major")
    assert valid is False
