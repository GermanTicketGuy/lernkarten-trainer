"""Laden und Speichern eines Decks als JSON (Aufgabenstellung 4.2).

Speicherformat (JSON):
    [
      {
        "question":      str,
        "answer":        str,
        "category":      str,
        "correct_count": int,
        "wrong_count":   int
      },
      ...
    ]

Fehlende Felder ``correct_count`` / ``wrong_count`` werden als 0 interpretiert.
Fehlerhafte oder unvollständige Dateien werfen ``StorageError``.
"""

from __future__ import annotations

import json
from pathlib import Path

from .deck import Deck


class StorageError(Exception):
    """Sammelfehler für Probleme beim Laden/Speichern eines Decks."""


def save_deck(deck: Deck, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(deck.to_list(), fh, ensure_ascii=False, indent=2)


def load_deck(path: str | Path) -> Deck:
    path = Path(path)
    if not path.exists():
        raise StorageError(f"Datei nicht gefunden: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise StorageError(f"Datei ist kein gültiges JSON: {path}") from exc

    try:
        return Deck.from_list(data)
    except (ValueError, TypeError) as exc:
        raise StorageError(f"Datei enthält ungültige Karten-Daten: {path}") from exc
