"""Einstiegspunkt für den Lernkarten-Trainer.

Aufruf:
    python lernkarten.py
    python lernkarten.py --file data/eigenes_deck.json
"""

from src.lernkarten.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
