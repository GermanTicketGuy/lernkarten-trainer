"""Verwaltung einer Sammlung von Lernkarten (Aufgabenstellung 4.1).

Ein Deck kapselt eine Liste von Karten und stellt CRUD-Operationen bereit:
- Karte hinzufügen
- Karte bearbeiten
- Karte entfernen
- Karten einer Kategorie anzeigen
"""

from __future__ import annotations

from typing import Iterable, Iterator

from .card import Card


class CardNotFoundError(LookupError):
    """Wird geworfen, wenn ein Index außerhalb des Decks angesprochen wird."""


class Deck:
    def __init__(self, cards: Iterable[Card] | None = None) -> None:
        self._cards: list[Card] = list(cards) if cards else []

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(self._cards)

    def __getitem__(self, index: int) -> Card:
        try:
            return self._cards[index]
        except IndexError as exc:
            raise CardNotFoundError(f"Keine Karte mit Index {index}.") from exc

    @property
    def cards(self) -> list[Card]:
        return list(self._cards)

    def add(self, card: Card) -> None:
        self._cards.append(card)

    def remove(self, index: int) -> Card:
        if not 0 <= index < len(self._cards):
            raise CardNotFoundError(f"Keine Karte mit Index {index}.")
        return self._cards.pop(index)

    def update(
        self,
        index: int,
        *,
        question: str | None = None,
        answer: str | None = None,
        category: str | None = None,
    ) -> Card:
        card = self[index]
        new_card = Card(
            question=question if question is not None else card.question,
            answer=answer if answer is not None else card.answer,
            category=category if category is not None else card.category,
            correct_count=card.correct_count,
            wrong_count=card.wrong_count,
        )
        self._cards[index] = new_card
        return new_card

    def filter_by_category(self, category: str) -> list[Card]:
        return [c for c in self._cards if c.category == category]

    def categories(self) -> list[str]:
        seen: dict[str, None] = {}
        for c in self._cards:
            seen.setdefault(c.category, None)
        return list(seen.keys())

    def to_list(self) -> list[dict]:
        return [c.to_dict() for c in self._cards]

    @classmethod
    def from_list(cls, data: list[dict]) -> "Deck":
        if not isinstance(data, list):
            raise ValueError("Deck-Daten müssen eine Liste sein.")
        return cls(Card.from_dict(item) for item in data)
