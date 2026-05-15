"""Lernsession und Wiederholungslogik (Aufgabenstellung 4.3 und 4.4).

Wiederholungslogik (gewichtetes Zufallsziehen):
    gewicht(karte) = 1 + 3 * falsch_anteil + bonus_neu

    - falsch_anteil  = wrong_count / (correct_count + wrong_count)
      ⇒ Karten mit hoher Fehlerquote haben höhere Priorität (Regel 3)
      ⇒ falsch beantwortete Karten werden häufiger gezogen (Regel 1)
      ⇒ richtig beantwortete Karten haben rel. niedrigeres Gewicht (Regel 2)
    - bonus_neu = 2.0, falls die Karte noch nie beantwortet wurde
      ⇒ neue Karten werden bevorzugt eingeplant (Regel 4)

Die Mindest­gewichtung von 1 stellt sicher, dass jede Karte ziehbar bleibt.
"""

from __future__ import annotations

import random
from typing import Sequence

from .card import Card
from .deck import Deck


NEW_CARD_BONUS = 2.0
WRONG_RATIO_WEIGHT = 3.0


def card_weight(card: Card) -> float:
    """Gewicht einer Karte für die Auswahl in einer Lernsession."""
    if card.total_attempts == 0:
        return 1.0 + NEW_CARD_BONUS
    wrong_ratio = card.wrong_count / card.total_attempts
    return 1.0 + WRONG_RATIO_WEIGHT * wrong_ratio


def pick_next_card(cards: Sequence[Card], rng: random.Random | None = None) -> Card:
    """Wählt die nächste Karte gewichtet zufällig aus.

    Wirft ``IndexError``, wenn keine Karten zur Auswahl stehen.
    """
    if not cards:
        raise IndexError("Keine Karten zur Auswahl.")
    rng = rng or random.Random()
    weights = [card_weight(c) for c in cards]
    return rng.choices(list(cards), weights=weights, k=1)[0]


class Session:
    """Eine Lernsession über ein Deck.

    Bewertungen (richtig/falsch) werden direkt in die Karten-Statistik geschrieben.
    """

    def __init__(self, deck: Deck, rng: random.Random | None = None) -> None:
        if len(deck) == 0:
            raise ValueError("Lernsession benötigt mindestens eine Karte.")
        self.deck = deck
        self._rng = rng or random.Random()
        self._answered: int = 0

    @property
    def answered(self) -> int:
        return self._answered

    def next_card(self) -> Card:
        return pick_next_card(self.deck.cards, self._rng)

    def grade(self, card: Card, correct: bool) -> None:
        """Speichert die Bewertung einer Karte (Aufgabenstellung 4.3)."""
        card.record_answer(correct)
        self._answered += 1
