from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field


VALID_QUALITIES = frozenset({
    "major", "minor", "dominant", "diminished", "augmented",
    "half-diminished", "sus2", "sus4", "diminished7", "major7", "minor7",
})

VALID_DEGREES = frozenset({2, 4, 5, 6, 7, 9, 11, 13})
VALID_ALTERATIONS = frozenset({-1, 0, 1})


@dataclass
class NoteRef:
    pitchClass: int   # 0–11
    spelling: str     # e.g. "C#", "Db"

    def __post_init__(self) -> None:
        if not (0 <= self.pitchClass <= 11):
            raise ValueError(f"pitchClass must be 0–11, got {self.pitchClass}")


@dataclass
class Extension:
    degree: int       # one of VALID_DEGREES
    alteration: int   # -1, 0, or +1

    def __post_init__(self) -> None:
        if self.degree not in VALID_DEGREES:
            raise ValueError(f"Invalid extension degree: {self.degree}")
        if self.alteration not in VALID_ALTERATIONS:
            raise ValueError(f"Invalid alteration: {self.alteration}")


@dataclass
class Chord:
    root: NoteRef
    quality: str
    extensions: list[Extension] = field(default_factory=list)
    bassNote: Optional[NoteRef] = None

    def __post_init__(self) -> None:
        if self.quality not in VALID_QUALITIES:
            raise ValueError(f"Invalid quality: {self.quality!r}")

    def to_dict(self) -> dict:
        return {
            "root": {"pitchClass": self.root.pitchClass, "spelling": self.root.spelling},
            "quality": self.quality,
            "extensions": [
                {"degree": e.degree, "alteration": e.alteration}
                for e in self.extensions
            ],
            "bassNote": (
                {"pitchClass": self.bassNote.pitchClass, "spelling": self.bassNote.spelling}
                if self.bassNote is not None else None
            ),
        }

    @staticmethod
    def from_dict(d: dict) -> "Chord":
        root = NoteRef(
            pitchClass=d["root"]["pitchClass"],
            spelling=d["root"]["spelling"],
        )
        extensions = [
            Extension(degree=e["degree"], alteration=e["alteration"])
            for e in d.get("extensions", [])
        ]
        bass_raw = d.get("bassNote")
        bassNote = (
            NoteRef(pitchClass=bass_raw["pitchClass"], spelling=bass_raw["spelling"])
            if bass_raw is not None else None
        )
        return Chord(root=root, quality=d["quality"], extensions=extensions, bassNote=bassNote)


_QUALITY_SUFFIX: dict[str, str] = {
    "major":           "",
    "minor":           "m",
    "dominant":        "7",
    "major7":          "maj7",
    "minor7":          "m7",
    "diminished":      "dim",
    "diminished7":     "dim7",
    "half-diminished": "m7b5",
    "augmented":       "aug",
    "sus2":            "sus2",
    "sus4":            "sus4",
}

_ALTERATION_PREFIX: dict[int, str] = {-1: "b", 0: "", 1: "#"}


def chord_to_name(chord: Chord) -> str:
    """Reconstruct the chord name string from a Chord dataclass."""
    name = chord.root.spelling + _QUALITY_SUFFIX.get(chord.quality, chord.quality)
    for ext in chord.extensions:
        prefix = _ALTERATION_PREFIX.get(ext.alteration, "")
        name += f"{prefix}{ext.degree}"
    if chord.bassNote is not None:
        name += f"/{chord.bassNote.spelling}"
    return name
