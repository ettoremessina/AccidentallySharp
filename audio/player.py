"""FluidSynth lifecycle and chord playback (block and arpeggio)."""

import time
import threading
import os

import fluidsynth

from audio.driver import detect_os_driver
from audio.midi import chord_to_midi_notes, MIDI_MIN, MIDI_MAX
from theory.chord import Chord

# Playback constants
BLOCK_VELOCITY = 80
BLOCK_DURATION_MS = 1500
ARPEGGIO_VELOCITY = 72
ARPEGGIO_NOTE_GAP_MS = 120
ARPEGGIO_SUSTAIN_MS = 400

SOUNDFONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "piano.sf2")
MIDI_CHANNEL = 0
BANK = 0
PRESET = 0  # Acoustic Grand Piano


class AudioPlayer:
    """Manages FluidSynth lifecycle and chord playback."""

    def __init__(self) -> None:
        self._fs: fluidsynth.Synth | None = None
        self._sfid: int = -1
        self._active_notes: set[int] = set()
        self._lock = threading.Lock()

    @property
    def is_ready(self) -> bool:
        """True if FluidSynth started and soundfont loaded successfully."""
        return self._fs is not None and self._sfid != -1

    def start(self) -> None:
        """Initialise FluidSynth. Raises RuntimeError on any failure."""
        sf_path = os.path.normpath(SOUNDFONT_PATH)
        if not os.path.isfile(sf_path):
            raise RuntimeError(
                f"Soundfont not found at: {sf_path}\n"
                "Place piano.sf2 in the assets/ directory."
            )
        driver = detect_os_driver()
        try:
            self._fs = fluidsynth.Synth(gain=0.5)
            self._fs.start(driver=driver)
        except Exception as e:
            self._fs = None
            raise RuntimeError(f"FluidSynth audio driver failed ({driver}): {e}") from e
        self._sfid = self._fs.sfload(sf_path)
        if self._sfid == -1:
            raise RuntimeError("Failed to load soundfont.")
        self._fs.program_select(MIDI_CHANNEL, self._sfid, BANK, PRESET)

    def stop(self) -> None:
        """Release all notes and shut down FluidSynth."""
        self._silence_all()
        if self._fs is not None:
            self._fs.delete()
            self._fs = None

    def _silence_all(self) -> None:
        """Call noteoff for every currently active note."""
        with self._lock:
            if self._fs is not None:
                for note in self._active_notes:
                    self._fs.noteoff(MIDI_CHANNEL, note)
            self._active_notes.clear()

    def _noteon(self, note: int, velocity: int) -> None:
        if self._fs is None:
            return
        note = max(MIDI_MIN, min(MIDI_MAX, note))
        self._fs.noteon(MIDI_CHANNEL, note, velocity)
        self._active_notes.add(note)

    def _noteoff(self, note: int) -> None:
        if self._fs is None:
            return
        self._fs.noteoff(MIDI_CHANNEL, note)
        self._active_notes.discard(note)

    def play_block(self, chord: Chord, octave: int = 3) -> None:
        """Play all chord notes simultaneously, then release after duration."""
        self._silence_all()
        notes = chord_to_midi_notes(chord, root_octave=octave)
        with self._lock:
            for note in notes:
                self._noteon(note, BLOCK_VELOCITY)
        time.sleep(BLOCK_DURATION_MS / 1000)
        with self._lock:
            for note in notes:
                self._noteoff(note)

    def play_arpeggio(self, chord: Chord, octave: int = 3) -> None:
        """Play chord notes bottom-to-top with overlapping sustain."""
        self._silence_all()
        notes = chord_to_midi_notes(chord, root_octave=octave)
        threads: list[threading.Thread] = []

        for note in notes:
            with self._lock:
                self._noteon(note, ARPEGGIO_VELOCITY)

            def _release(n: int = note) -> None:
                time.sleep(ARPEGGIO_SUSTAIN_MS / 1000)
                with self._lock:
                    self._noteoff(n)

            t = threading.Thread(target=_release, daemon=True)
            t.start()
            threads.append(t)
            time.sleep(ARPEGGIO_NOTE_GAP_MS / 1000)

        for t in threads:
            t.join()
