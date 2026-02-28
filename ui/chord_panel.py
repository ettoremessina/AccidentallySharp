"""Chord input panel: user types a chord name and triggers playback."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDialog, QScrollArea,
)
from PyQt6.QtCore import pyqtSignal, Qt

from theory.parser import parse_chord_name
from theory.chord import Chord

_LEGEND_HTML = """
<style>
  body  { font-family: sans-serif; font-size: 13px; }
  h3    { margin: 12px 0 4px 0; color: #89b4fa; }
  table { border-collapse: collapse; width: 100%; }
  td    { padding: 2px 8px 2px 0; vertical-align: top; }
  td.ex { font-family: monospace; font-size: 13px; color: #cdd6f4; white-space: nowrap; }
  td.desc { color: #a6adc8; }
  p.note  { color: #a6adc8; margin: 6px 0 0 0; font-size: 12px; }
</style>

<h3>Roots</h3>
<p class="note">A &nbsp;B &nbsp;C &nbsp;D &nbsp;E &nbsp;F &nbsp;G &nbsp;&nbsp;—&nbsp;
add <b>#</b> or <b>b</b> for accidentals:&nbsp; C# &nbsp;Db &nbsp;F# &nbsp;Bb …</p>

<h3>Triads</h3>
<table>
  <tr><td class="ex">C</td>      <td class="desc">major</td></tr>
  <tr><td class="ex">Cm</td>     <td class="desc">minor</td></tr>
  <tr><td class="ex">Cdim</td>   <td class="desc">diminished</td></tr>
  <tr><td class="ex">Caug</td>   <td class="desc">augmented</td></tr>
  <tr><td class="ex">Csus2</td>  <td class="desc">suspended 2nd</td></tr>
  <tr><td class="ex">Csus4</td>  <td class="desc">suspended 4th &nbsp;(also: Csus)</td></tr>
  <tr><td class="ex">C5</td>     <td class="desc">power chord (root + fifth)</td></tr>
</table>

<h3>Seventh chords</h3>
<table>
  <tr><td class="ex">C7</td>     <td class="desc">dominant 7th</td></tr>
  <tr><td class="ex">Cmaj7</td>  <td class="desc">major 7th &nbsp;(also: CM7)</td></tr>
  <tr><td class="ex">Cm7</td>    <td class="desc">minor 7th</td></tr>
  <tr><td class="ex">Cdim7</td>  <td class="desc">diminished 7th</td></tr>
  <tr><td class="ex">Cm7b5</td>  <td class="desc">half-diminished &nbsp;(also: Cø)</td></tr>
</table>

<h3>Extended chords</h3>
<table>
  <tr><td class="ex">C6</td>     <td class="desc">major 6th</td></tr>
  <tr><td class="ex">C9</td>     <td class="desc">dominant 9th (includes minor 7th)</td></tr>
  <tr><td class="ex">Cadd9</td>  <td class="desc">major triad + 9th, no 7th</td></tr>
  <tr><td class="ex">C11</td>    <td class="desc">dominant 11th</td></tr>
  <tr><td class="ex">C13</td>    <td class="desc">dominant 13th</td></tr>
  <tr><td class="ex">Cm9</td>    <td class="desc">minor 9th</td></tr>
  <tr><td class="ex">Cmaj9</td>  <td class="desc">major 9th</td></tr>
</table>

<h3>Alterations</h3>
<table>
  <tr><td class="ex">C7b9</td>   <td class="desc">dominant 7th, flat 9</td></tr>
  <tr><td class="ex">C7#9</td>   <td class="desc">dominant 7th, sharp 9</td></tr>
  <tr><td class="ex">C7#11</td>  <td class="desc">dominant 7th, sharp 11 (Lydian dominant)</td></tr>
</table>

<h3>Slash chords</h3>
<table>
  <tr><td class="ex">C/E</td>    <td class="desc">C major with E in the bass</td></tr>
  <tr><td class="ex">G/B</td>    <td class="desc">G major with B in the bass</td></tr>
  <tr><td class="ex">Am/G</td>   <td class="desc">A minor with G in the bass</td></tr>
</table>

<p class="note">All chord types can be used with any root note.<br>
Chord names are case-sensitive: <b>C</b> ≠ <b>Cm</b>, &nbsp;<b>Cmaj7</b> ≠ <b>CM7</b>.</p>
"""


class ChordPanel(QWidget):
    """Panel for entering and playing a single chord."""

    chord_played = pyqtSignal(object)        # emits Chord
    chord_added = pyqtSignal(object, int)   # emits (Chord, octave)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_chord: Chord | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Section header
        title = QLabel("Play a chord")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        # Chord name label + input
        layout.addWidget(QLabel("Chord name:"))
        self._chord_input = QLineEdit()
        self._chord_input.setPlaceholderText("e.g.  C  Am  G7  Cmaj7  G/B")
        self._chord_input.setMinimumHeight(36)
        self._chord_input.returnPressed.connect(self._on_play)
        layout.addWidget(self._chord_input)

        # Play button row (Play + help button)
        btn_row = QHBoxLayout()
        play_btn = QPushButton("▶  Play")
        play_btn.clicked.connect(self._on_play)
        btn_row.addWidget(play_btn, stretch=1)
        help_btn = QPushButton("?")
        help_btn.setFixedWidth(34)
        help_btn.setToolTip("Show chord name reference")
        help_btn.clicked.connect(self._on_show_legend)
        btn_row.addWidget(help_btn)
        layout.addLayout(btn_row)

        # Playback mode + octave row
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Block", "Arpeggio"])
        mode_row.addWidget(self._mode_combo)
        mode_row.addSpacing(16)
        mode_row.addWidget(QLabel("Octave:"))
        self._octave_combo = QComboBox()
        self._octave_combo.addItems([str(o) for o in range(1, 7)])  # 1–6
        self._octave_combo.setCurrentText("3")  # default
        mode_row.addWidget(self._octave_combo)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Status / error label
        self._status_label = QLabel("")
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        layout.addStretch()

        # Add to progression button
        add_btn = QPushButton("+ Add to progression")
        add_btn.clicked.connect(self._on_add)
        layout.addWidget(add_btn)

    def _on_play(self) -> None:
        text = self._chord_input.text().strip()
        try:
            chord = parse_chord_name(text)
            self._current_chord = chord
            self._status_label.setText("")
            self.chord_played.emit(chord)
        except ValueError as e:
            self._status_label.setText(f"? {e}")

    def _on_add(self) -> None:
        if self._current_chord is not None:
            self.chord_added.emit(self._current_chord, self.playback_octave())

    def _on_show_legend(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Chord name reference")
        dlg.setMinimumSize(400, 500)

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)

        label = QLabel(_LEGEND_HTML)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        label.setContentsMargins(12, 8, 12, 8)

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        dlg.exec()

    def playback_mode(self) -> str:
        return self._mode_combo.currentText().lower()

    def playback_octave(self) -> int:
        return int(self._octave_combo.currentText())
