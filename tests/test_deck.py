"""Unit-Tests für Deck (Aufgabenstellung 4.1, 6: Hinzufügen/Entfernen, Randfall leeres Deck)."""

import unittest

from src.lernkarten.card import Card
from src.lernkarten.deck import CardNotFoundError, Deck


def _card(q="q", a="a", c="Mathe"):
    return Card(q, a, c)


class TestDeckBasics(unittest.TestCase):
    def test_empty_deck(self):
        """Randfall: leere Kartensammlung."""
        deck = Deck()
        self.assertEqual(len(deck), 0)
        self.assertEqual(deck.cards, [])
        self.assertEqual(deck.categories(), [])

    def test_add_card(self):
        deck = Deck()
        deck.add(_card())
        self.assertEqual(len(deck), 1)

    def test_remove_card(self):
        deck = Deck([_card("a", "1", "X"), _card("b", "2", "X")])
        removed = deck.remove(0)
        self.assertEqual(removed.question, "a")
        self.assertEqual(len(deck), 1)
        self.assertEqual(deck[0].question, "b")

    def test_remove_invalid_index_raises(self):
        deck = Deck()
        with self.assertRaises(CardNotFoundError):
            deck.remove(0)

    def test_update_card_preserves_stats(self):
        deck = Deck([_card()])
        deck[0].record_answer(True)
        deck.update(0, answer="neue Antwort")
        self.assertEqual(deck[0].answer, "neue Antwort")
        self.assertEqual(deck[0].correct_count, 1)

    def test_update_invalid_index_raises(self):
        deck = Deck()
        with self.assertRaises(CardNotFoundError):
            deck.update(5, question="x")


class TestDeckCategories(unittest.TestCase):
    def test_filter_by_category(self):
        deck = Deck([
            _card("a", "1", "Mathe"),
            _card("b", "2", "Bio"),
            _card("c", "3", "Mathe"),
        ])
        mathe = deck.filter_by_category("Mathe")
        self.assertEqual(len(mathe), 2)
        self.assertTrue(all(c.category == "Mathe" for c in mathe))

    def test_filter_unknown_category(self):
        deck = Deck([_card()])
        self.assertEqual(deck.filter_by_category("Chemie"), [])

    def test_categories_unique_and_ordered(self):
        deck = Deck([
            _card("a", "1", "Mathe"),
            _card("b", "2", "Bio"),
            _card("c", "3", "Mathe"),
        ])
        self.assertEqual(deck.categories(), ["Mathe", "Bio"])


class TestDeckSerialization(unittest.TestCase):
    def test_roundtrip(self):
        deck = Deck([_card("a", "1", "X"), _card("b", "2", "Y")])
        restored = Deck.from_list(deck.to_list())
        self.assertEqual(restored.to_list(), deck.to_list())

    def test_from_list_rejects_non_list(self):
        with self.assertRaises(ValueError):
            Deck.from_list({"not": "a list"})  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
