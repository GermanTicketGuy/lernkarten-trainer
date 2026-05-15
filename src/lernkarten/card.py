"""Datenklasse für eine einzelne Lernkarte.

Pflichtfelder laut Aufgabenstellung (Abschnitt 3):
- Frage
- Antwort
- Kategorie
- statistische Informationen (richtige/falsche Antworten)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class Card:
    question: str
    answer: str
    category: str
    correct_count: int = 0
    wrong_count: int = 0

    def __post_init__(self) -> None:
        if not self.question or not self.question.strip():
            raise ValueError("Frage darf nicht leer sein.")
        if not self.answer or not self.answer.strip():
            raise ValueError("Antwort darf nicht leer sein.")
        if not self.category or not self.category.strip():
            raise ValueError("Kategorie darf nicht leer sein.")
        if self.correct_count < 0 or self.wrong_count < 0:
            raise ValueError("Zähler dürfen nicht negativ sein.")

    @property
    def total_attempts(self) -> int:
        return self.correct_count + self.wrong_count

    @property
    def success_rate(self) -> float:
        """Erfolgsquote als Wert in [0, 1]. Unbeantwortete Karten -> 0.0."""
        if self.total_attempts == 0:
            return 0.0
        return self.correct_count / self.total_attempts

    def record_answer(self, correct: bool) -> None:
        """Bewertet eine Antwort und aktualisiert die Statistik."""
        if correct:
            self.correct_count += 1
        else:
            self.wrong_count += 1

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        required = {"question", "answer", "category"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Fehlende Felder in Karte: {sorted(missing)}")
        return cls(
            question=data["question"],
            answer=data["answer"],
            category=data["category"],
            correct_count=int(data.get("correct_count", 0)),
            wrong_count=int(data.get("wrong_count", 0)),
        )
