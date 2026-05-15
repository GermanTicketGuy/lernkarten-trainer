"""Auswertungen über ein Deck (Aufgabenstellung 4.5)."""

from __future__ import annotations

from .card import Card
from .deck import Deck


def total_cards(deck: Deck) -> int:
    return len(deck)


def cards_per_category(deck: Deck) -> dict[str, int]:
    result: dict[str, int] = {}
    for card in deck:
        result[card.category] = result.get(card.category, 0) + 1
    return result


def overall_success_rate(deck: Deck) -> float:
    """Erfolgsquote über alle Karten. Bei 0 Versuchen: 0.0 (kein Div-by-zero)."""
    correct = sum(c.correct_count for c in deck)
    wrong = sum(c.wrong_count for c in deck)
    total = correct + wrong
    if total == 0:
        return 0.0
    return correct / total


def success_rate_per_category(deck: Deck) -> dict[str, float]:
    sums: dict[str, list[int]] = {}
    for c in deck:
        bucket = sums.setdefault(c.category, [0, 0])
        bucket[0] += c.correct_count
        bucket[1] += c.wrong_count
    return {
        cat: (correct / (correct + wrong)) if (correct + wrong) > 0 else 0.0
        for cat, (correct, wrong) in sums.items()
    }


def hardest_cards(deck: Deck, limit: int = 5, min_attempts: int = 1) -> list[Card]:
    """Liefert die Karten mit der niedrigsten Erfolgsquote (mind. ``min_attempts``).

    Sortierung: zuerst niedrigste Erfolgsquote, dann meiste Falschantworten.
    """
    candidates = [c for c in deck if c.total_attempts >= min_attempts]
    candidates.sort(key=lambda c: (c.success_rate, -c.wrong_count))
    return candidates[:limit]


def best_cards(deck: Deck, limit: int = 5, min_attempts: int = 1) -> list[Card]:
    """Liefert die Karten mit der höchsten Erfolgsquote (mind. ``min_attempts``)."""
    candidates = [c for c in deck if c.total_attempts >= min_attempts]
    candidates.sort(key=lambda c: (-c.success_rate, -c.correct_count))
    return candidates[:limit]


def total_answers(deck: Deck) -> int:
    """Gesamtzahl der bisher gegebenen Antworten (richtig + falsch)."""
    return sum(c.correct_count + c.wrong_count for c in deck)
