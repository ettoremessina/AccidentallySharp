# AccidentallySharp ♯

A chord progression explorer for music beginners.
Build progressions by playing chords on a virtual piano, hear them with real piano sound,
and let an AI suggest what to play next — or generate an entire progression for you.

The name reflects the spirit of the app: discovering music almost by accident,
without taking theory too seriously.

---

## Features

- **Virtual piano** — click notes to build chords; block or arpeggio playback
- **Chord builder** — choose root, quality, and extensions from simple dropdowns
- **Octave control** — pick the octave for each chord individually
- **Chord legend** — built-in reference for all supported chord types
- **Progression builder** — assemble a sequence of chords, reorder or delete entries, play it back
- **AI suggestions** — ask the LLM for the next chord that fits your key and style
- **AI progression generation** — describe a mood and get a full progression in one click
- **Multi-provider LLM** — works with OpenAI, Anthropic, Ollama, or LM Studio

---

## Requirements

- Python 3.11+
- FluidSynth (system library — see below)
- A piano soundfont bundled at `assets/piano.sf2`

### Install FluidSynth

| Platform | Command |
|----------|---------|
| macOS    | `brew install fluid-synth` |
| Ubuntu/Debian | `sudo apt install fluidsynth` |
| Windows  | Download from [fluidsynth.org](https://www.fluidsynth.org) and add to PATH |

---

## Installation

```bash
git clone https://github.com/ettoremessina/AccidentallySharp.git
cd AccidentallySharp

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## Running

```bash
# With OpenAI (default)
export OPENAI_API_KEY=sk-...
python main.py

# With Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python main.py --llm anthropic

# With a local Ollama server
python main.py --llm ollama --llm-model llama3

# With LM Studio
python main.py --llm lmstudio --llm-model mistralai/ministral-3b --lmstudio-url http://localhost:1234/v1
```

### All CLI options

```
--llm {openai,anthropic,ollama,lmstudio}   LLM provider (default: openai)
--llm-model MODEL                          Override the model name
--ollama-url URL                           Ollama base URL (default: http://localhost:11434/v1)
--lmstudio-url URL                         LM Studio base URL (default: http://localhost:1234/v1)
```

---

## Project structure

```
AccidentallySharp/
├── main.py                   # Entry point
├── theory/                   # Music theory — pure, no I/O
│   ├── chord.py              # Chord dataclass + chord_to_name()
│   ├── parser.py             # parse_chord_name(s) -> Chord
│   ├── intervals.py          # chord_to_pitch_classes(chord) -> set[int]
│   └── enharmonic.py         # Enharmonic spelling utilities
├── llm/                      # LLM integration
│   ├── providers.py          # OpenAI / Anthropic / Ollama / LMStudio
│   ├── client.py             # Provider dispatcher
│   ├── context_builder.py    # Builds harmonic context for LLM calls
│   └── validator.py          # Validates LLM suggestions before display
├── audio/                    # Audio playback (FluidSynth)
│   ├── midi.py               # chord_to_midi_notes(chord, octave)
│   ├── player.py             # Block and arpeggio playback
│   └── driver.py             # Auto-detect OS audio driver
├── ui/                       # PyQt6 interface
│   ├── main_window.py
│   ├── chord_panel.py        # Piano / chord builder panel
│   ├── progression_panel.py  # Progression + AI suggestions panel
│   └── styles.qss            # Dark theme (Catppuccin-inspired)
├── assets/
│   └── piano.sf2             # Bundled soundfont
└── tests/
    ├── test_parser.py
    ├── test_intervals.py
    ├── test_midi.py
    └── test_validator.py
```

---

## Running tests

```bash
pytest tests/
```

No audio hardware or API key required to run the test suite.

---

## Credits

The bundled soundfont `assets/piano.sf2` is **GeneralUser GS** by
[S. Christian Collins](https://www.schristiancollins.com/generaluser),
used with permission under its free license.

---

## License

MIT
