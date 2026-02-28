# AccidentallySharp

A Python desktop application that helps music beginners generate and explore
chord progressions. The name reflects the spirit of the app: discovering music
almost by accident, without taking theory too seriously.

## Target User

Music beginners. The UI must be approachable and non-intimidating.
Prefer simplicity over completeness at every design decision.

## Stack

- **Language**: Python
- **UI**: PyQt6
- **Audio**: FluidSynth via pyfluidsynth, piano soundfont (.sf2) bundled
- **LLM at runtime**: used to suggest next chords in a progression
  - Default provider: **OpenAI** (`gpt-4o-mini`)
  - Also supported: Anthropic, Ollama, LM Studio

## Music Notation

The application uses standard English music notation throughout:
notes are A B C D E F G with # and b accidentals.
This applies to all user input, display, and internal string representations.

## Internal Chord Representation

All chord data is stored and passed between layers using this structure:

```python
{
    "root": {
        "pitchClass": 0,   # int 0–11: C=0, C#/Db=1, D=2, D#/Eb=3, E=4,
                            # F=5, F#/Gb=6, G=7, G#/Ab=8, A=9, A#/Bb=10, B=11
        "spelling": "C"    # str: preserves user's enharmonic choice
    },
    "quality": "major",    # major | minor | dominant | diminished |
                            # augmented | half-diminished | sus2 | sus4
    "extensions": [
        {
            "degree": 7,       # int: 2 | 4 | 5 | 6 | 7 | 9 | 11 | 13
            "alteration": 0    # int: 0 = natural, -1 = flat, +1 = sharp
        }
    ],
    "bassNote": None       # None or same structure as root (for slash chords)
}
```

Never represent a chord as a raw string or a plain list of notes internally.
Always use this structure when passing chord data between modules.

## Project Structure

```
AccidentallySharp/
│
├── main.py                   # Entry point
│
├── theory/                   # Layer 1 — Music theory (pure, no I/O)
│   ├── __init__.py
│   ├── chord.py              # Chord dataclass + validation
│   ├── parser.py             # parse_chord_name(s: str) -> Chord
│   ├── intervals.py          # chord_to_pitch_classes(chord) -> set[int]
│   └── enharmonic.py         # Enharmonic spelling utilities
│
├── llm/                      # Layer 2 — LLM integration
│   ├── __init__.py
│   ├── context_builder.py    # build_harmonic_context(...) -> dict
│   ├── providers.py          # LLMProvider base class + OpenAI/Anthropic/Ollama/LMStudio
│   ├── client.py             # configure(provider) + get_chord_suggestions()
│   └── validator.py          # validate_suggestion(...) -> bool
│
├── audio/                    # Layer 3 — Audio playback
│   ├── __init__.py
│   ├── midi.py               # chord_to_midi_notes(chord, octave) -> list[int]
│   ├── player.py             # FluidSynth lifecycle, block + arpeggio playback
│   └── driver.py             # detect_os_driver() -> str
│
├── ui/                       # Layer 4 — PyQt6 interface
│   ├── __init__.py
│   ├── main_window.py
│   ├── chord_panel.py
│   ├── progression_panel.py
│   └── styles.qss
│
├── assets/
│   └── piano.sf2             # Bundled soundfont — do not load from system paths
│
├── tests/
│   ├── test_parser.py
│   ├── test_intervals.py
│   ├── test_midi.py
│   └── test_validator.py
│
├── requirements.txt
└── CLAUDE.md
```

## Layer Rules

These rules are strict. Violations must be refactored immediately.

- `theory/` imports nothing from `llm/`, `audio/`, or `ui/`
- `llm/` imports only from `theory/`
- `audio/` imports only from `theory/`
- `ui/` is the only layer that imports from all others
- No FluidSynth calls outside `audio/`
- No LLM API calls outside `llm/`
- No PyQt6 imports outside `ui/`

## Audio

Two playback modes:

**Block chord**: all notes triggered simultaneously.
Default velocity: 80. Default duration: 1500ms.

**Arpeggio**: notes triggered bottom to top in sequence.
Default velocity: 72. Note gap: 120ms. Note sustain: 400ms.

MIDI note range: clamp all notes to 21–108 (piano range).
Default voicing: root in octave 3 (C3 = MIDI 48), close voicing upward.

FluidSynth audio driver must be selected automatically based on OS:
- macOS: `coreaudio`
- Linux: `alsa`
- Windows: `dsound`

Always call noteoff for all active notes before starting a new chord.
Maintain a set of currently active MIDI note numbers.

## LLM Integration

### Provider selection

The provider is chosen at startup via `--llm`. `llm/client.configure()` is
called once in `main.py` before the window is created; the rest of the app
calls `get_chord_suggestions()` without knowing which provider is active.

```
python main.py --llm openai                          # default, needs OPENAI_API_KEY
python main.py --llm anthropic                       # needs ANTHROPIC_API_KEY
python main.py --llm ollama                          # Ollama running locally
python main.py --llm lmstudio                        # LM Studio running locally
python main.py --llm ollama --llm-model mistral      # override model
python main.py --llm ollama --ollama-url http://...  # override URL
```

| Provider  | Default model    | Auth              | Base URL                       |
|-----------|-----------------|-------------------|--------------------------------|
| openai    | gpt-4o-mini     | OPENAI_API_KEY    | api.openai.com (SDK default)   |
| anthropic | claude-sonnet-4-6 | ANTHROPIC_API_KEY | SDK default                    |
| ollama    | llama3          | none              | http://localhost:11434/v1      |
| lmstudio  | local-model     | none              | http://localhost:1234/v1       |

Ollama and LM Studio expose an OpenAI-compatible API; the same
`_OpenAICompatibleProvider` base class handles all three.

All LLM API calls are isolated inside `llm/`. No provider-specific imports
appear anywhere else.

### Harmonic context

The LLM is called at runtime to suggest the next chord given a tonal context.

Context sent to the LLM:
```json
{
  "key": { "root": "C", "mode": "major" },
  "progression": [
    { "degree": 1, "chord": "C" },
    { "degree": 6, "chord": "Am" }
  ],
  "currentChord": { "degree": 4, "chord": "F" },
  "styleHint": "pop"
}
```

Include the last 3–4 chords in the progression history.
Request 2–3 suggestions per call, each with a plain-language `reason` field.

Validation before display:
1. Diatonic membership → show unconditionally
2. Known borrowed chord (bVII in major, major IV in minor) → show with label
3. Same as currentChord → reject silently and retry
4. Anything else → reject silently and retry

## Subagents

Five specialized agents are available in `.claude/agents/`:

- **chord-theory-expert**: chord structure, nomenclature, parsing rules,
  interval formulas, enharmonic handling, edge cases
- **harmonic-progressions-expert**: progression logic, LLM context design,
  diatonic validation, beginner-appropriate suggestion strategy
- **chord-to-audio-expert**: MIDI mapping, FluidSynth API, voicing strategy,
  timing values, OS driver selection
- **code-reviewer**: layer separation, domain correctness, Python quality,
  LLM and FluidSynth specific checks
- **test-generator**: pytest cases for theory, MIDI mapping, and LLM
  validation — no audio hardware required

## Key Domain Rules

- `C7` is dominant seventh (M3 + m7), never major seventh
- `Cdim7` has a doubly-flatted seventh — not the same as `Cm7b5`
- `Csus` without a number means `Csus4` by convention
- `C9` implies a minor seventh — it is not just root + ninth
- `Cadd9` is major triad + ninth WITHOUT the seventh
- pitchClass is used for all computations; spelling is used only for display
- Slash chord bass note goes in `bassNote`, never in `extensions`