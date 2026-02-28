"""Parse a chord name string into a Chord dataclass."""

import re
from theory.chord import Chord, NoteRef, Extension
from theory.enharmonic import spelling_to_pitch_class

# Regex tokens
_ROOT_RE = re.compile(r'^([A-G][#b]?)')
_SLASH_RE = re.compile(r'/([A-G][#b]?)$')

# Quality keyword mappings (order matters — longer tokens first)
_QUALITY_TOKENS: list[tuple[str, str]] = [
    ("maj7",        "major7"),
    ("M7",          "major7"),
    ("Δ7",          "major7"),
    ("maj",         "major7"),   # "Cmaj" without number → treated as major triad below
    ("min7",        "minor7"),
    ("m7b5",        "half-diminished"),
    ("m7",          "minor7"),
    ("-7",          "minor7"),
    ("dim7",        "diminished7"),
    ("°7",          "diminished7"),
    ("ø7",          "half-diminished"),
    ("ø",           "half-diminished"),
    ("min",         "minor"),
    ("m",           "minor"),
    ("-",           "minor"),
    ("dim",         "diminished"),
    ("°",           "diminished"),
    ("aug",         "augmented"),
    ("+",           "augmented"),
    ("sus4",        "sus4"),
    ("sus2",        "sus2"),
    ("sus",         "sus4"),     # "Csus" → sus4 by convention
    ("M",           "major"),    # standalone capital M (after maj7/M7 already matched)
]

# Extension pattern: optional (b|#|maj|add) followed by a degree number
_EXT_RE = re.compile(r'(b|#|maj|add)?(\d+)')


def _parse_extensions(token: str) -> list[Extension]:
    """Parse the extensions/alterations part of a chord name."""
    extensions: list[Extension] = []
    pos = 0
    while pos < len(token):
        m = _EXT_RE.match(token, pos)
        if not m:
            pos += 1
            continue
        prefix, degree_str = m.group(1) or "", m.group(2)
        degree = int(degree_str)
        pos = m.end()

        if prefix == "add":
            # addN: natural extension, no seventh implied
            if degree in (9, 11, 13, 2, 4, 6):
                extensions.append(Extension(degree=degree, alteration=0))
        elif prefix == "maj":
            # majN: major quality on the extension (e.g. maj9 → natural 9)
            if degree in (6, 7, 9, 11, 13):
                extensions.append(Extension(degree=degree, alteration=0))
        elif prefix == "b":
            if degree in (2, 4, 5, 6, 7, 9, 11, 13):
                extensions.append(Extension(degree=degree, alteration=-1))
        elif prefix == "#":
            if degree in (2, 4, 5, 6, 7, 9, 11, 13):
                extensions.append(Extension(degree=degree, alteration=1))
        else:
            # bare number
            if degree == 5:
                # power chord — represented as extension degree 5 alteration 0
                extensions.append(Extension(degree=5, alteration=0))
            elif degree in (6, 9, 11, 13):
                extensions.append(Extension(degree=degree, alteration=0))
            elif degree in (2, 4):
                extensions.append(Extension(degree=degree, alteration=0))
            elif degree == 7:
                # bare "7" without quality prefix handled by caller
                extensions.append(Extension(degree=7, alteration=0))

    return extensions


def parse_chord_name(s: str) -> Chord:
    """
    Parse a chord name string into a Chord.

    Raises ValueError on invalid input.
    """
    s = s.strip()
    if not s:
        raise ValueError("Empty chord name")

    # Extract slash bass note first (so it doesn't confuse root parsing)
    bass_note: NoteRef | None = None
    slash_m = _SLASH_RE.search(s)
    if slash_m:
        bass_spelling = slash_m.group(1)
        try:
            bass_pc = spelling_to_pitch_class(bass_spelling)
        except ValueError:
            raise ValueError(f"Invalid bass note in slash chord: {bass_spelling!r}")
        bass_note = NoteRef(pitchClass=bass_pc, spelling=bass_spelling)
        s = s[:slash_m.start()]

    # Extract root
    root_m = _ROOT_RE.match(s)
    if not root_m:
        raise ValueError(f"Cannot parse root from chord name: {s!r}")
    root_spelling = root_m.group(1)
    try:
        root_pc = spelling_to_pitch_class(root_spelling)
    except ValueError:
        raise ValueError(f"Invalid root note: {root_spelling!r}")
    root = NoteRef(pitchClass=root_pc, spelling=root_spelling)

    remainder = s[root_m.end():]

    # Match quality token
    quality = "major"
    matched_quality_token = ""
    for token, q in _QUALITY_TOKENS:
        if remainder.startswith(token):
            quality = q
            matched_quality_token = token
            remainder = remainder[len(token):]
            break

    # Special case: "maj" without a following number → plain major triad
    if matched_quality_token == "maj" and not remainder:
        quality = "major"

    # Now parse extensions from remainder
    extensions: list[Extension] = []

    if remainder:
        # Handle bare numbers that imply quality changes
        # e.g. "7" on a plain major chord → dominant7
        # "9" → dominant with m7 + M9
        bare_num_m = re.match(r'^(\d+)', remainder)
        if bare_num_m and quality == "major":
            n = int(bare_num_m.group(1))
            if n == 7:
                quality = "dominant"
                remainder = remainder[bare_num_m.end():]
            elif n == 9:
                quality = "dominant"
                extensions.append(Extension(degree=7, alteration=0))
                extensions.append(Extension(degree=9, alteration=0))
                remainder = remainder[bare_num_m.end():]
            elif n == 11:
                quality = "dominant"
                extensions.append(Extension(degree=7, alteration=0))
                extensions.append(Extension(degree=9, alteration=0))
                extensions.append(Extension(degree=11, alteration=0))
                remainder = remainder[bare_num_m.end():]
            elif n == 13:
                quality = "dominant"
                extensions.append(Extension(degree=7, alteration=0))
                extensions.append(Extension(degree=9, alteration=0))
                extensions.append(Extension(degree=11, alteration=0))
                extensions.append(Extension(degree=13, alteration=0))
                remainder = remainder[bare_num_m.end():]
            elif n == 6:
                extensions.append(Extension(degree=6, alteration=0))
                remainder = remainder[bare_num_m.end():]
            elif n == 5:
                # Power chord: strip the third from quality
                quality = "major"
                extensions = [Extension(degree=5, alteration=0)]
                remainder = remainder[bare_num_m.end():]

        extensions += _parse_extensions(remainder)

    # Ensure major7/minor7/dominant quality doesn't get an extra degree-7 extension
    # (the quality already encodes the seventh)
    seen_7 = {e.degree for e in extensions}
    if quality in ("major7", "minor7", "dominant", "diminished7", "half-diminished"):
        extensions = [e for e in extensions if e.degree != 7]

    return Chord(root=root, quality=quality, extensions=extensions, bassNote=bass_note)
