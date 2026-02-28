"""Progression panel: displays the chord progression and LLM suggestions."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QLineEdit, QSpinBox,
)
from PyQt6.QtCore import pyqtSignal, Qt

from theory.chord import Chord, chord_to_name
from theory.parser import parse_chord_name
from llm.context_builder import build_harmonic_context
from llm.client import get_chord_suggestions, get_chord_progression
from llm.validator import validate_suggestion

KEYS = [
    "C", "G", "D", "A", "E", "B", "F#",
    "F", "Bb", "Eb", "Ab", "Db",
]
MODES = ["major", "minor"]


class ProgressionPanel(QWidget):
    """Panel for managing chord progression and LLM suggestions."""

    suggestion_selected = pyqtSignal(str)          # emits chord name string
    progression_play_requested = pyqtSignal(list)  # emits list[(Chord, int)]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._progression: list[dict] = []              # {"degree": int, "chord": str}
        self._progression_chords: list[tuple[Chord, int]] = []  # (Chord, octave)
        self._last_chord: Chord | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Section header
        title = QLabel("Progression & suggestions")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        # Key selector row
        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("Key:"))
        self._key_combo = QComboBox()
        self._key_combo.addItems(KEYS)
        key_row.addWidget(self._key_combo)
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(MODES)
        key_row.addWidget(self._mode_combo)
        key_row.addStretch()
        layout.addLayout(key_row)

        # Style / mood input
        layout.addWidget(QLabel("Style or mood (for LLM):"))
        self._style_input = QLineEdit()
        self._style_input.setPlaceholderText("e.g.  melancholic jazz,  uplifting pop,  bossa nova…")
        self._style_input.returnPressed.connect(self._on_generate_progression)
        layout.addWidget(self._style_input)

        # Generate row: chord count spinbox + Generate button
        gen_row = QHBoxLayout()
        gen_row.addWidget(QLabel("Chords:"))
        self._count_spin = QSpinBox()
        self._count_spin.setRange(2, 16)
        self._count_spin.setValue(4)
        self._count_spin.setFixedWidth(52)
        gen_row.addWidget(self._count_spin)
        gen_row.addStretch()
        gen_btn = QPushButton("Generate")
        gen_btn.setToolTip("Ask the LLM to generate chords in the chosen key and style")
        gen_btn.clicked.connect(self._on_generate_progression)
        gen_row.addWidget(gen_btn)
        layout.addLayout(gen_row)

        # Progression list
        layout.addWidget(QLabel("Progression:"))
        self._progression_list = QListWidget()
        layout.addWidget(self._progression_list)

        # Progression action buttons row
        prog_btn_row = QHBoxLayout()
        play_prog_btn = QPushButton("▶  Play")
        play_prog_btn.clicked.connect(self._on_play_progression)
        prog_btn_row.addWidget(play_prog_btn, stretch=1)
        delete_btn = QPushButton("Delete selected")
        delete_btn.clicked.connect(self._on_delete_selected)
        prog_btn_row.addWidget(delete_btn, stretch=1)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear)
        prog_btn_row.addWidget(clear_btn, stretch=1)
        layout.addLayout(prog_btn_row)

        # Suggest next chord button
        suggest_btn = QPushButton("Suggest next chord")
        suggest_btn.clicked.connect(self._on_suggest)
        layout.addWidget(suggest_btn)

        # Suggestions list
        layout.addWidget(QLabel("Suggestions:"))
        self._suggestions_list = QListWidget()
        self._suggestions_list.itemDoubleClicked.connect(self._on_suggestion_clicked)
        layout.addWidget(self._suggestions_list)

        self._suggest_status = QLabel("")
        self._suggest_status.setObjectName("statusLabel")
        self._suggest_status.setWordWrap(True)
        layout.addWidget(self._suggest_status)

    # ------------------------------------------------------------------ #
    # Public                                                               #
    # ------------------------------------------------------------------ #

    def add_chord(self, chord: Chord, octave: int = 3) -> None:
        """Add a chord to the progression."""
        self._last_chord = chord
        self._progression_chords.append((chord, octave))
        name = chord_to_name(chord)
        entry = {"degree": 0, "chord": name}
        self._progression.append(entry)
        label = name if octave == 3 else f"{name}  (oct {octave})"
        self._progression_list.addItem(QListWidgetItem(label))

    # ------------------------------------------------------------------ #
    # Slots                                                                #
    # ------------------------------------------------------------------ #

    def _on_play_progression(self) -> None:
        if self._progression_chords:
            self.progression_play_requested.emit(list(self._progression_chords))

    def _on_delete_selected(self) -> None:
        row = self._progression_list.currentRow()
        if row < 0:
            return
        self._progression_list.takeItem(row)
        del self._progression[row]
        del self._progression_chords[row]
        # Keep _last_chord in sync with the new last entry
        if self._progression_chords:
            self._last_chord = self._progression_chords[-1][0]
        else:
            self._last_chord = None

    def _on_clear(self) -> None:
        self._progression.clear()
        self._progression_chords.clear()
        self._progression_list.clear()
        self._suggestions_list.clear()
        self._suggest_status.setText("")
        self._last_chord = None

    def _on_generate_progression(self) -> None:
        key_root = self._key_combo.currentText()
        key_mode = self._mode_combo.currentText()
        style_hint = self._style_input.text().strip() or "pop"
        count = self._count_spin.value()

        self._suggest_status.setText("Generating progression…")
        try:
            chord_names = get_chord_progression(key_root, key_mode, style_hint, count)
        except Exception as e:
            self._suggest_status.setText(f"LLM error: {e}")
            return

        if not chord_names:
            self._suggest_status.setText("LLM returned no chords. Try again.")
            return

        # Append to existing progression (do NOT clear first)
        skipped: list[str] = []
        for name in chord_names:
            try:
                chord = parse_chord_name(name)
                self.add_chord(chord)
            except ValueError:
                skipped.append(name)

        if skipped:
            self._suggest_status.setText(
                f"Done. Skipped unrecognised chords: {', '.join(skipped)}"
            )
        else:
            self._suggest_status.setText(
                "Chords added! Press ▶ Play to hear the progression."
            )

    def _on_suggest(self) -> None:
        if self._last_chord is None:
            self._suggest_status.setText("Add at least one chord first.")
            return

        key_root = self._key_combo.currentText()
        key_mode = self._mode_combo.currentText()
        context = build_harmonic_context(
            key_root=key_root,
            key_mode=key_mode,
            progression=self._progression[:-1],
            current_chord=self._last_chord,
            current_degree=self._progression[-1].get("degree", 0),
        )

        self._suggest_status.setText("Asking LLM…")
        try:
            raw_suggestions = get_chord_suggestions(context)
        except Exception as e:
            self._suggest_status.setText(f"LLM error: {e}")
            return

        self._suggestions_list.clear()
        shown = 0
        for s in raw_suggestions:
            valid, label = validate_suggestion(
                s,
                current_chord_spelling=self._last_chord.root.spelling,
                key_root=key_root,
                key_mode=key_mode,
            )
            if not valid:
                continue
            chord_name = s.get("chord", "")
            reason = s.get("reason", "")
            display = chord_name
            if label:
                display += f"  [{label}]"
            if reason:
                display += f"  — {reason}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, chord_name)
            self._suggestions_list.addItem(item)
            shown += 1

        if shown == 0:
            self._suggest_status.setText("No valid suggestions returned. Try again.")
        else:
            self._suggest_status.setText("Double-click a suggestion to use it.")

    def _on_suggestion_clicked(self, item: QListWidgetItem) -> None:
        chord_name = item.data(Qt.ItemDataRole.UserRole)
        if chord_name:
            self.suggestion_selected.emit(chord_name)
