"""Einzeltasten-Eingabe für die Menü-Navigation (POSIX + Windows).

``read_key()`` liefert einen normalisierten Bezeichner statt eines Rohzeichens:

    'up' | 'down' | 'left' | 'right' | 'enter' | 'esc' | 'backspace' |
    'q' | 't' | '0' .. '9' | '<char>' | 'unknown'

Auf POSIX-Systemen wird stdin temporär in den cbreak-Modus geschaltet, sodass
Tasten direkt (ohne Enter) erkannt werden. Pfeiltasten erzeugen Escape-Sequenzen
der Form ``ESC [ A`` (oben), ``ESC [ B`` (unten), die hier zerlegt werden.

Die Funktion ist absichtlich klein gehalten: für die Tests wird sie nicht
genutzt — die CLI nimmt stattdessen einen ``key_fn`` als Parameter entgegen.
"""

from __future__ import annotations

import os
import sys


def _read_key_posix() -> str:  # pragma: no cover - benötigt echtes Terminal
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = os.read(fd, 1).decode("utf-8", errors="replace")
        if ch == "\x1b":
            # Escape-Sequenz: bis zu zwei weitere Bytes lesen.
            seq = ch
            try:
                seq += os.read(fd, 2).decode("utf-8", errors="replace")
            except OSError:
                pass
            mapping = {
                "\x1b[A": "up",
                "\x1b[B": "down",
                "\x1b[C": "right",
                "\x1b[D": "left",
            }
            return mapping.get(seq, "esc")
        if ch in ("\r", "\n"):
            return "enter"
        if ch == "\x7f":
            return "backspace"
        if ch == "\x03":  # Ctrl-C
            raise KeyboardInterrupt
        if ch == " ":
            return "space"
        return ch.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _read_key_windows() -> str:  # pragma: no cover - Windows-only
    import msvcrt

    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):
        code = msvcrt.getwch()
        return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(code, "unknown")
    if ch in ("\r", "\n"):
        return "enter"
    if ch == "\x1b":
        return "esc"
    if ch == "\x08":
        return "backspace"
    if ch == "\x03":
        raise KeyboardInterrupt
    return ch.lower()


def read_key() -> str:
    """Liest eine einzelne Taste und liefert einen normalisierten Bezeichner."""
    if os.name == "nt":  # pragma: no cover
        return _read_key_windows()
    return _read_key_posix()
