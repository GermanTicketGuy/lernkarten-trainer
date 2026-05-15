"""Unit-Tests für Statistik (Aufgabenstellung 4.5, 6: Division durch null, leeres Deck)."""

import unittest

from src.lernkarten.card import Card
from src.lernkarten.deck import Deck
from src.lernkarten.statistics import (
    best_cards,
    cards_per_category,
    hardest_cards,
    overall_success_rate,
    success_rate_per_category,
    total_answers,
    total_cards,
)


class TestStatistics(unittest.TestCase):
    def setUp(self):
        self.deck = Deck([
            Card("a", "1", "Mathe", correct_count=4, wrong_count=1),  # 80%
            Card("b", "2", "Mathe", correct_count=1, wrong_count=3),  # 25%
            Card("c", "3", "Bio", correct_count=2, wrong_count=2),    # 50%
            Card("d", "4", "Bio"),                                     # neu
        ])

    def test_total_cards(self):
        self.assertEqual(total_cards(self.deck), 4)

    def test_cards_per_category(self):
        self.assertEqual(cards_per_category(self.deck), {"Mathe": 2, "Bio": 2})

    def test_overall_success_rate(self):
        # 4+1+2 richtig / (5+4+4) gesamt = 7/13
        self.assertAlmostEqual(overall_success_rate(self.deck), 7 / 13)

    def test_success_rate_per_category(self):
        rates = success_rate_per_category(self.deck)
        self.assertAlmostEqual(rates["Mathe"], 5 / 9)
        self.assertAlmostEqual(rates["Bio"], 2 / 4)

    def test_hardest_cards(self):
        hardest = hardest_cards(self.deck, limit=2)
        self.assertEqual(hardest[0].question, "b")  # 25%

    def test_overall_success_rate_empty_deck(self):
        """Randfall: leeres Deck — keine Division durch null."""
        self.assertEqual(overall_success_rate(Deck()), 0.0)

    def test_overall_success_rate_no_attempts(self):
        """Randfall: alle Karten neu, kein Versuch — keine Division durch null."""
        deck = Deck([Card("q", "a", "c")])
        self.assertEqual(overall_success_rate(deck), 0.0)

    def test_cards_per_category_empty(self):
        self.assertEqual(cards_per_category(Deck()), {})

    def test_hardest_cards_skips_unanswered(self):
        deck = Deck([Card("q", "a", "c")])
        self.assertEqual(hardest_cards(deck), [])

    def test_best_cards_sorted_descending(self):
        best = best_cards(self.deck, limit=2)
        self.assertEqual(best[0].question, "a")  # 80%
        self.assertEqual(best[1].question, "c")  # 50%

    def test_best_cards_skips_unanswered(self):
        deck = Deck([Card("q", "a", "c")])
        self.assertEqual(best_cards(deck), [])

    def test_total_answers(self):
        self.assertEqual(total_answers(self.deck), 5 + 4 + 4 + 0)

    def test_total_answers_empty(self):
        self.assertEqual(total_answers(Deck()), 0)


if __name__ == "__main__":
    unittest.main()
