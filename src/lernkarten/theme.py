"""Farb-Themes für die Terminal-Oberfläche.

Übernommen aus dem Web-Prototyp (terminal.jsx). Farben werden als 24-Bit-ANSI
Escape-Sequenzen ausgegeben (von macOS Terminal, iTerm2, Linux-Terminals und
modernen Windows-Terminals unterstützt).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    fg: tuple[int, int, int]
    accent: tuple[int, int, int]
    dim: tuple[int, int, int]
    muted: tuple[int, int, int]
    light: bool = False

    @property
    def warn(self) -> tuple[int, int, int]:
        """Warnfarbe für 'schwierigste' Karten (Lachs/Korallrot)."""
        return (255, 138, 128)


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


THEMES: dict[str, Theme] = {
    "matrix":  Theme("Matrix",     _hex("3bff8a"), _hex("9cff9c"), _hex("1d6b3a"), _hex("0e3a20")),
    "amber":   Theme("Amber CRT",  _hex("ffb000"), _hex("ffd87a"), _hex("7a5400"), _hex("3a2400")),
    "ice":     Theme("Arctic",     _hex("9fdcff"), _hex("dff5ff"), _hex("3a6e8a"), _hex("0a3045")),
    "paper":   Theme("Paperwhite", _hex("1a1a1a"), _hex("c2371e"), _hex("7a6a4a"), _hex("c4b890"), light=True),
    "synth":   Theme("Synthwave",  _hex("ff7ec3"), _hex("5af2ff"), _hex("6a3a8a"), _hex("2a1342")),
    "classic": Theme("Klassisch",  _hex("e5e5e5"), _hex("5fff5f"), _hex("5a6a5a"), _hex("1a221a")),
}

DEFAULT_THEME = "ice"


RESET = "\033[0m"
BOLD = "\033[1m"


def fg(rgb: tuple[int, int, int]) -> str:
    """24-Bit-ANSI-Vordergrundfarbe."""
    r, g, b = rgb
    return f"\033[38;2;{r};{g};{b}m"


def paint(text: str, rgb: tuple[int, int, int], bold: bool = False) -> str:
    prefix = (BOLD if bold else "") + fg(rgb)
    return f"{prefix}{text}{RESET}"
