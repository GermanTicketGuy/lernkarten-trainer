"""Unit-Tests für die Card-Klasse (Aufgabenstellung 6: Erstellen/Verändern von Karten,
Bewertung einer Antwort, Aktualisierung des Lernstatus, Division durch null)."""

import unittest

from src.lernkarten.card import Card


class TestCardCreation(unittest.TestCase):
    def test_create_valid_card(self):
        card = Card(question="2+2?", answer="4", category="Mathe")
        self.assertEqual(card.question, "2+2?")
        self.assertEqual(card.answer, "4")
        self.assertEqual(card.category, "Mathe")
        self.assertEqual(card.correct_count, 0)
        self.assertEqual(card.wrong_count, 0)

    def test_empty_question_raises(self):
        with self.assertRaises(ValueError):
            Card(question="   ", answer="4", category="Mathe")

    def test_empty_answer_raises(self):
        with self.assertRaises(ValueError):
            Card(question="2+2?", answer="", category="Mathe")

    def test_empty_category_raises(self):
        with self.assertRaises(ValueError):
            Card(question="2+2?", answer="4", category="")

    def test_negative_counts_raise(self):
        with self.assertRaises(ValueError):
            Card(question="q", answer="a", category="c", correct_count=-1)


class TestCardAnswering(unittest.TestCase):
    def test_record_correct(self):
        card = Card("q", "a", "c")
        card.record_answer(True)
        self.assertEqual(card.correct_count, 1)
        self.assertEqual(card.wrong_count, 0)

    def test_record_wrong(self):
        card = Card("q", "a", "c")
        card.record_answer(False)
        self.assertEqual(card.wrong_count, 1)
        self.assertEqual(card.correct_count, 0)

    def test_success_rate_division_by_zero(self):
        """Randfall: Erfolgsquote bei 0 Versuchen darf nicht abstürzen."""
        card = Card("q", "a", "c")
        self.assertEqual(card.success_rate, 0.0)

    def test_success_rate_mixed(self):
        card = Card("q", "a", "c")
        card.record_answer(True)
        card.record_answer(True)
        card.record_answer(False)
        self.assertAlmostEqual(card.success_rate, 2 / 3)


class TestCardSerialization(unittest.TestCase):
    def test_roundtrip(self):
        original = Card("q", "a", "c", correct_count=3, wrong_count=2)
        restored = Card.from_dict(original.to_dict())
        self.assertEqual(restored, original)

    def test_from_dict_missing_fields(self):
        with self.assertRaises(ValueError):
            Card.from_dict({"question": "q", "answer": "a"})  # category fehlt


if __name__ == "__main__":
    unittest.main()
