"""Unit-Tests für Storage (Aufgabenstellung 4.2, 6:
nicht vorhandene Datei, fehlerhafte Datei, Roundtrip)."""

import json
import tempfile
import unittest
from pathlib import Path

from src.lernkarten.card import Card
from src.lernkarten.deck import Deck
from src.lernkarten.storage import StorageError, load_deck, save_deck


class TestStorage(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_save_and_load_roundtrip(self):
        deck = Deck([
            Card("2+2?", "4", "Mathe", correct_count=1),
            Card("Hauptstadt von DE?", "Berlin", "Geo"),
        ])
        path = self.tmp / "deck.json"
        save_deck(deck, path)
        loaded = load_deck(path)
        self.assertEqual(loaded.to_list(), deck.to_list())

    def test_load_missing_file(self):
        """Randfall: Laden einer nicht vorhandenen Datei."""
        with self.assertRaises(StorageError):
            load_deck(self.tmp / "gibt-es-nicht.json")

    def test_load_invalid_json(self):
        """Randfall: Laden einer fehlerhaften Datei (kaputtes JSON)."""
        path = self.tmp / "kaputt.json"
        path.write_text("{ das ist kein json", encoding="utf-8")
        with self.assertRaises(StorageError):
            load_deck(path)

    def test_load_json_with_missing_card_fields(self):
        """Randfall: JSON ist gültig, Karte aber unvollständig."""
        path = self.tmp / "luecke.json"
        path.write_text(json.dumps([{"question": "q", "answer": "a"}]), encoding="utf-8")
        with self.assertRaises(StorageError):
            load_deck(path)

    def test_load_json_root_not_list(self):
        path = self.tmp / "objekt.json"
        path.write_text(json.dumps({"karten": []}), encoding="utf-8")
        with self.assertRaises(StorageError):
            load_deck(path)

    def test_save_creates_parent_directory(self):
        path = self.tmp / "sub" / "deck.json"
        save_deck(Deck(), path)
        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
