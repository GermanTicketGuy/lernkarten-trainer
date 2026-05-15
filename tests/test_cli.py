"""Tests für die interaktive CLI (Aufgabenstellung 5).

Die ``run``-Funktion akzeptiert ``input_fn``/``output_fn``/``key_fn`` als
Parameter. Wir füttern Eingaben aus Listen und sammeln die Ausgaben.

Hinweise zur Bedienung:
- ``key_fn`` simuliert einzelne Tastendrücke (Pfeil hoch/runter, Enter, '1'..'6',
  't', 'q'). Auch der "Beliebige Taste"-Pause-Prompt liest aus ``key_fn``.
- ``input_fn`` wird in den Aktions-Screens für Texteingabe verwendet.
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.lernkarten.cli import run


class CliHarness:
    """Simuliert Tastatureingaben (Text + Einzeltasten) und sammelt Ausgaben."""

    def __init__(self, texts: list[str], keys: list[str]):
        self._texts = list(texts)
        self._keys = list(keys)
        self.outputs: list[str] = []

    def input_fn(self, prompt: str = "") -> str:
        if not self._texts:
            raise AssertionError(
                f"Mehr Texteingaben angefordert als bereitgestellt. Prompt: {prompt!r}"
            )
        return self._texts.pop(0)

    def key_fn(self) -> str:
        if not self._keys:
            raise AssertionError("Mehr Tastendrücke angefordert als bereitgestellt.")
        return self._keys.pop(0)

    def output_fn(self, line: str = "") -> None:
        self.outputs.append(line)

    @property
    def all_output(self) -> str:
        return "\n".join(self.outputs)


class TestCliMenu(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.deck_file = self.tmp / "deck.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_then_list_then_quit(self):
        """Karte über Direktwahl '1' anlegen, dann '2' = Anzeigen, dann 'q' = Beenden."""
        h = CliHarness(
            texts=["2+2?", "4", "Mathe", ""],
            keys=["1", "enter", "2", "enter", "q"],
        )
        rc = run(self.deck_file, h.input_fn, h.output_fn, h.key_fn)
        self.assertEqual(rc, 0)
        self.assertIn("2+2?", h.all_output)
        self.assertIn("Gespeichert", h.all_output)
        data = json.loads(self.deck_file.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 1)

    def test_arrow_navigation_to_stats(self):
        """Pfeil-unten 5x bringt die Auswahl von 'Karte hinzufügen' zu 'Statistik anzeigen'."""
        h = CliHarness(
            texts=[],
            keys=["down", "down", "down", "down", "down", "enter", "enter", "q"],
        )
        rc = run(self.deck_file, h.input_fn, h.output_fn, h.key_fn)
        self.assertEqual(rc, 0)
        self.assertIn("STATISTIK", h.all_output)

    def test_vim_bindings(self):
        """j/k navigieren genauso wie down/up."""
        h = CliHarness(
            texts=[""],  # Kategorie-Filter beim Anzeigen leer lassen
            keys=["j", "j", "k", "enter", "enter", "q"],  # Index 1 = "Karten anzeigen"
        )
        rc = run(self.deck_file, h.input_fn, h.output_fn, h.key_fn)
        self.assertEqual(rc, 0)
        self.assertIn("KARTEN", h.all_output)

    def test_stats_on_empty_deck_no_crash(self):
        """Randfall: Statistik auf leerem Deck — keine Division durch null, kein Absturz."""
        h = CliHarness(texts=[], keys=["6", "enter", "q"])
        rc = run(self.deck_file, h.input_fn, h.output_fn, h.key_fn)
        self.assertEqual(rc, 0)
        self.assertIn("Karten gesamt", h.all_output)
        self.assertIn("Erfolgsquote", h.all_output)
        self.assertIn("Antworten total", h.all_output)

    def test_remove_on_empty_deck(self):
        h = CliHarness(texts=[], keys=["4", "enter", "q"])
        rc = run(self.deck_file, h.input_fn, h.output_fn, h.key_fn)
        self.assertEqual(rc, 0)
        self.assertIn("Keine Karten vorhanden", h.all_output)

    def test_train_can_be_aborted_with_x(self):
        """Lernsession lässt sich mit 'x' vorzeitig beenden."""
        h = CliHarness(
            texts=[
                "q", "a", "Mathe",   # Karte anlegen
                "10",                 # Lernsession: Anzahl
                "x",                  # direkt abbrechen am Antwort-Prompt
            ],
            keys=["1", "enter", "5", "enter", "q"],
        )
        rc = run(self.deck_file, h.input_fn, h.output_fn, h.key_fn)
        self.assertEqual(rc, 0)
        self.assertIn("abgebrochen", h.all_output)

    def test_corrupt_file_is_reported_not_crashing(self):
        """Randfall: fehlerhafte Datei beim Start — Programm meldet sich, stürzt nicht ab."""
        self.deck_file.write_text("{kein json", encoding="utf-8")
        h = CliHarness(texts=[], keys=["q"])
        rc = run(self.deck_file, h.input_fn, h.output_fn, h.key_fn)
        self.assertEqual(rc, 0)
        self.assertIn("Fehler beim Laden", h.all_output)


if __name__ == "__main__":
    unittest.main()
