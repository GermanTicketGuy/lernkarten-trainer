"""Unit-Tests für Session und Wiederholungslogik (Aufgabenstellung 4.3, 4.4, 6)."""

import random
import unittest
from collections import Counter

from src.lernkarten.card import Card
from src.lernkarten.deck import Deck
from src.lernkarten.session import Session, card_weight, pick_next_card


class TestCardWeight(unittest.TestCase):
    def test_new_card_has_bonus(self):
        new = Card("q", "a", "c")
        attempted_perfect = Card("q", "a", "c", correct_count=5, wrong_count=0)
        self.assertGreater(card_weight(new), card_weight(attempted_perfect))

    def test_wrong_increases_weight(self):
        good = Card("q", "a", "c", correct_count=10, wrong_count=0)
        bad = Card("q", "a", "c", correct_count=1, wrong_count=9)
        self.assertGreater(card_weight(bad), card_weight(good))

    def test_weight_minimum(self):
        """Auch eine perfekt beantwortete Karte bleibt ziehbar (Gewicht > 0)."""
        good = Card("q", "a", "c", correct_count=20, wrong_count=0)
        self.assertGreater(card_weight(good), 0.0)


class TestPickNextCard(unittest.TestCase):
    def test_empty_raises(self):
        with self.assertRaises(IndexError):
            pick_next_card([])

    def test_difficult_cards_drawn_more_often(self):
        """Statistischer Test: schwierige Karte wird häufiger gezogen als eine perfekte."""
        easy = Card("easy", "a", "c", correct_count=20, wrong_count=0)
        hard = Card("hard", "a", "c", correct_count=1, wrong_count=19)
        rng = random.Random(42)
        counts = Counter(pick_next_card([easy, hard], rng).question for _ in range(1000))
        self.assertGreater(counts["hard"], counts["easy"])


class TestSession(unittest.TestCase):
    def test_empty_deck_rejected(self):
        with self.assertRaises(ValueError):
            Session(Deck())

    def test_grade_updates_card_and_counter(self):
        deck = Deck([Card("q", "a", "c")])
        session = Session(deck, rng=random.Random(0))
        card = session.next_card()
        session.grade(card, correct=True)
        self.assertEqual(card.correct_count, 1)
        self.assertEqual(session.answered, 1)

    def test_grade_wrong(self):
        deck = Deck([Card("q", "a", "c")])
        session = Session(deck, rng=random.Random(0))
        session.grade(deck[0], correct=False)
        self.assertEqual(deck[0].wrong_count, 1)


if __name__ == "__main__":
    unittest.main()
