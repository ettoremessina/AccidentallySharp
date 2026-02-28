"""AccidentallySharp — entry point."""

import sys
import argparse
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt
import llm.client as llm_client
from ui.main_window import MainWindow


def _make_icon() -> QIcon:
    """Generate the app icon: sharp sign ♯ on a dark background."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor("#1e1e2e"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    font = QFont("Helvetica Neue", 38, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#89b4fa"))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♯")

    painter.end()
    return QIcon(pixmap)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AccidentallySharp — chord progression explorer for beginners",
    )
    parser.add_argument(
        "--llm",
        choices=["openai", "anthropic", "ollama", "lmstudio"],
        default="openai",
        metavar="PROVIDER",
        help="LLM provider to use: openai (default), anthropic, ollama, lmstudio",
    )
    parser.add_argument(
        "--llm-model",
        default=None,
        metavar="MODEL",
        dest="llm_model",
        help="Override the model name (e.g. gpt-4o, llama3, mistral)",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434/v1",
        metavar="URL",
        dest="ollama_url",
        help="Ollama base URL (default: http://localhost:11434/v1)",
    )
    parser.add_argument(
        "--lmstudio-url",
        default="http://localhost:1234/v1",
        metavar="URL",
        dest="lmstudio_url",
        help="LM Studio base URL (default: http://localhost:1234/v1)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Build kwargs for the provider constructor
    kwargs: dict = {}
    if args.llm_model:
        kwargs["model"] = args.llm_model
    if args.llm == "ollama":
        kwargs.setdefault("base_url", args.ollama_url)
    elif args.llm == "lmstudio":
        kwargs.setdefault("base_url", args.lmstudio_url)

    llm_client.configure(args.llm, **kwargs)

    app = QApplication(sys.argv)
    app.setApplicationName("AccidentallySharp")
    app.setWindowIcon(_make_icon())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
