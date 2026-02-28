"""Main application window."""

import sys
import threading
import traceback

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt

from ui.chord_panel import ChordPanel
from ui.progression_panel import ProgressionPanel
from theory.chord import Chord
from audio.player import AudioPlayer


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AccidentallySharp")
        self.setMinimumSize(800, 500)

        self._player = AudioPlayer()
        try:
            self._player.start()
        except Exception as e:
            QMessageBox.warning(self, "Audio Warning", str(e))

        self._build_ui()
        self._connect_signals()
        self._apply_styles()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        self._chord_panel = ChordPanel()
        self._progression_panel = ProgressionPanel()

        layout.addWidget(self._chord_panel, stretch=1)
        layout.addWidget(self._progression_panel, stretch=1)

    def _connect_signals(self) -> None:
        self._chord_panel.chord_played.connect(self._on_chord_played)
        self._chord_panel.chord_added.connect(self._progression_panel.add_chord)
        self._progression_panel.suggestion_selected.connect(
            self._on_suggestion_selected
        )
        self._progression_panel.progression_play_requested.connect(
            self._on_progression_play
        )

    def _apply_styles(self) -> None:
        import os
        qss_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        if os.path.isfile(qss_path):
            with open(qss_path) as f:
                self.setStyleSheet(f.read())

    def _on_chord_played(self, chord: Chord) -> None:
        if not self._player.is_ready:
            QMessageBox.warning(self, "Audio not ready",
                                "Audio failed to initialise. Check the warning shown at startup.")
            return
        mode = self._chord_panel.playback_mode()
        octave = self._chord_panel.playback_octave()
        player_fn = self._player.play_arpeggio if mode == "arpeggio" else self._player.play_block

        def _run() -> None:
            try:
                player_fn(chord, octave=octave)
            except Exception:
                traceback.print_exc(file=sys.stderr)

        threading.Thread(target=_run, daemon=True).start()

    def _on_progression_play(self, chord_octave_pairs: list) -> None:
        if not self._player.is_ready:
            QMessageBox.warning(self, "Audio not ready",
                                "Audio failed to initialise. Check the warning shown at startup.")
            return
        mode = self._chord_panel.playback_mode()
        player_fn = self._player.play_arpeggio if mode == "arpeggio" else self._player.play_block

        def _run() -> None:
            for chord, octave in chord_octave_pairs:
                try:
                    player_fn(chord, octave=octave)
                except Exception:
                    traceback.print_exc(file=sys.stderr)

        threading.Thread(target=_run, daemon=True).start()

    def _on_suggestion_selected(self, chord_name: str) -> None:
        self._chord_panel._chord_input.setText(chord_name)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._player.stop()
        super().closeEvent(event)
