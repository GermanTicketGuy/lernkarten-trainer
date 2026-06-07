"""Interaktive Kommandozeilen-Oberfläche für den Lernkarten-Trainer
(Aufgabenstellung 5).

Die Oberfläche orientiert sich am Web-Prototyp (terminal.jsx von Claude Design)
und bringt dessen Look in den Terminal:

- ANSI-Shadow-Banner ("LERNKARTEN")
- 6 Farb-Themes (matrix, amber, ice, paper, synth, classic) per 24-Bit-ANSI
- Unicode-Boxen mit Titel, Hinweis-Zeile, Status-Zeile
- Akzentuierte Prompts und Hint-Texte

Alle I/O-Funktionen sind über ``input_fn`` / ``output_fn`` injizierbar, damit
die Menüabläufe in Unit-Tests deterministisch ansteuerbar sind.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Callable

from .card import Card
from .deck import CardNotFoundError, Deck
from .keyboard import read_key
from .session import Session
from .statistics import (
    best_cards,
    cards_per_category,
    hardest_cards,
    overall_success_rate,
    success_rate_per_category,
    total_answers,
    total_cards,
)
from .storage import StorageError, load_deck, save_deck
from .theme import DEFAULT_THEME, THEMES, Theme, paint


DEFAULT_PATH = Path("data/deck.json")
WIDTH = 78  # Box-Innenbreite in Zeichen

InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]
KeyFn = Callable[[], str]


# ─── ASCII Title (ANSI Shadow figlet, aus terminal.jsx übernommen) ──────────
TITLE_BIG = r"""
██╗     ███████╗██████╗ ███╗   ██╗██╗  ██╗ █████╗ ██████╗ ████████╗███████╗███╗   ██╗
██║     ██╔════╝██╔══██╗████╗  ██║██║ ██╔╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝████╗  ██║
██║     █████╗  ██████╔╝██╔██╗ ██║█████╔╝ ███████║██████╔╝   ██║   █████╗  ██╔██╗ ██║
██║     ██╔══╝  ██╔══██╗██║╚██╗██║██╔═██╗ ██╔══██║██╔══██╗   ██║   ██╔══╝  ██║╚██╗██║
███████╗███████╗██║  ██║██║ ╚████║██║  ██╗██║  ██║██║  ██║   ██║   ███████╗██║ ╚████║
╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝
""".strip("\n")

SUBTITLE = "░▒▓ T R A I N E R ▓▒░   ·   spaced-repetition flashcards   v1.1.0"

# Box-Glyphen
H, V = "─", "│"
TL, TR, BL, BR = "┌", "┐", "└", "┘"
LTEE, RTEE = "├", "┤"


# ─── Bildschirm-Helfer ─────────────────────────────────────────────────────
def _clear(out: OutputFn) -> None:
    """Bildschirm leeren (ANSI: \\033[2J = Bildschirm löschen, \\033[H = Cursor nach links oben)."""
    out("\033[2J\033[H")


def _hline(width: int = WIDTH) -> str:
    return TL + H * (width - 2) + TR


def _bline(width: int = WIDTH) -> str:
    return BL + H * (width - 2) + BR


def _title_line(title: str, theme: Theme, width: int = WIDTH) -> str:
    title_part = f"{H} {paint(title, theme.accent, bold=True)} "
    raw_len = len(title) + 4  # `── title ──`
    fill = H * max(1, width - 2 - raw_len)
    return TL + title_part + fill + TR


def _row(content: str, raw_visible_len: int, theme: Theme, width: int = WIDTH) -> str:
    """Eine Zeile innerhalb einer Box. ``raw_visible_len`` ist die Länge ohne ANSI-Codes."""
    inner = width - 4  # 2x Rand + 2x Padding
    pad = max(0, inner - raw_visible_len)
    border = paint(V, theme.dim)
    return f"{border} {content}{' ' * pad} {border}"


# ─── Banner & Statuszeile ───────────────────────────────────────────────────
def _banner(theme: Theme, out: OutputFn) -> None:
    out(paint(TITLE_BIG, theme.accent, bold=True))
    out(paint(SUBTITLE, theme.dim))
    out("")


def _statusline(deck: Deck, path: Path, screen: str, theme: Theme, out: OutputFn) -> None:
    time = datetime.now().strftime("%H:%M")
    parts = [
        f"Datei: {paint(str(path), theme.fg)}",
        f"Karten: {paint(str(len(deck)), theme.fg)}",
        f"Modus: {paint(screen, theme.accent)}",
        f"Theme: {paint(theme.name, theme.fg)}",
    ]
    sep = paint(" │ ", theme.dim)
    line = sep.join(parts) + sep + paint(time, theme.dim)
    out(line)
    out(paint(H * WIDTH, theme.dim))


def _hint(text: str, theme: Theme, out: OutputFn) -> None:
    out(paint("  " + text, theme.dim))


def _pause(key_fn: KeyFn, theme: Theme, out: OutputFn) -> None:
    out(paint("\n  ▸ Beliebige Taste zurück zum Menü", theme.dim))
    key_fn()


def _hotkey_bar(theme: Theme, out: OutputFn, *, in_menu: bool = True) -> None:
    sep = paint("│", theme.dim)
    parts: list[str] = []
    if in_menu:
        parts.append(f"{paint('↑↓', theme.accent)} navigieren")
        parts.append(f"{paint('Enter', theme.accent)} wählen")
        parts.append(f"{paint('1-6', theme.accent)} Direktwahl")
    parts.append(f"{paint('T', theme.accent)} Theme")
    parts.append(f"{paint('Q', theme.accent)} Beenden")
    out(paint("  ", theme.dim) + f"  {sep}  ".join(parts))


def _prompt(inp: InputFn, label: str, theme: Theme) -> str:
    return inp(paint(f"  {label}", theme.accent))


# ─── Laden / Theme-Wahl ─────────────────────────────────────────────────────
def _load_or_empty(path: Path, theme: Theme, out: OutputFn) -> Deck:
    if not path.exists():
        return Deck()
    try:
        return load_deck(path)
    except StorageError as exc:
        out(paint(f"  ✗ Fehler beim Laden: {exc}", theme.accent))
        out(paint("  Es wird mit einem leeren Deck weitergearbeitet.", theme.dim))
        return Deck()


def _action_theme(theme_key: str, inp: InputFn, out: OutputFn) -> str:
    theme = THEMES[theme_key]
    out(paint("  ┐ Theme wählen", theme.accent))
    out("")
    keys = list(THEMES.keys())
    for i, key in enumerate(keys, start=1):
        marker = "●" if key == theme_key else "○"
        out(f"  {paint(marker, theme.accent)} [{i}] {THEMES[key].name}")
    out("")
    raw = _prompt(inp, "Nummer wählen (leer = unverändert): » ", theme).strip()
    if not raw:
        return theme_key
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(keys):
            return keys[idx]
    except ValueError:
        pass
    out(paint("  ✗ Ungültige Eingabe.", theme.accent))
    return theme_key


# ─── Menü-Aktionen ──────────────────────────────────────────────────────────
MENU_ITEMS: list[tuple[str, str, str]] = [
    ("1", "Karte hinzufügen",    "neue Vorder-/Rückseite anlegen"),
    ("2", "Karten anzeigen",     "gesamte Deck-Liste durchsuchen"),
    ("3", "Karte bearbeiten",    "bestehende Karte editieren"),
    ("4", "Karte löschen",       "Karte aus dem Deck entfernen"),
    ("5", "Lernsession starten", "Karten der Reihe nach abfragen"),
    ("6", "Statistik anzeigen",  "Erfolgsquote pro Karte"),
]


def _print_menu(theme: Theme, selected: int, out: OutputFn) -> None:
    out(_title_line("HAUPTMENÜ", theme))
    border = paint(V, theme.dim)
    out(f"{border}{' ' * (WIDTH - 2)}{border}")
    for i, (key, label, hint) in enumerate(MENU_ITEMS):
        is_sel = i == selected
        marker = paint("▶", theme.accent, bold=True) if is_sel else " "
        key_part = paint(f"[{key}]", theme.accent, bold=True)
        if is_sel:
            label_part = paint(label, theme.accent, bold=True)
        else:
            label_part = label
        hint_part = paint(f"{hint} ›", theme.dim)
        visible = 2 + len(f"[{key}]") + 2 + len(label) + 2 + len(hint) + 2 + 1
        content = f"{marker} {key_part}  {label_part}  {hint_part}"
        out(_row(content, visible - 1, theme))
    out(f"{border}{' ' * (WIDTH - 2)}{border}")
    out(_bline())


def _action_add(deck: Deck, inp: InputFn, out: OutputFn, theme: Theme) -> None:
    out(_title_line("NEUE KARTE", theme))
    _hint("[1/3] Frage  ·  [2/3] Antwort  ·  [3/3] Kategorie", theme, out)
    out("")
    question = _prompt(inp, "?  ", theme).strip()
    answer = _prompt(inp, ">  ", theme).strip()
    category = _prompt(inp, "#  ", theme).strip()
    try:
        deck.add(Card(question, answer, category))
        out(paint(f"\n  ✓ Karte hinzugefügt. Deck enthält jetzt {len(deck)} Karte(n).", theme.accent))
    except ValueError as exc:
        out(paint(f"\n  ✗ Fehler: {exc}", theme.accent))


def _action_list(deck: Deck, inp: InputFn, out: OutputFn, theme: Theme) -> None:
    out(_title_line("KARTEN", theme))
    filter_cat = _prompt(inp, "Kategorie filtern (leer = alle): ", theme).strip()
    out("")
    if len(deck) == 0:
        _hint("(Keine Karten vorhanden.)", theme, out)
        return
    shown = 0
    for i, c in enumerate(deck):
        if filter_cat and c.category != filter_cat:
            continue
        idx = paint(f"[{i:>3}]", theme.accent)
        cat = paint(f"({c.category})", theme.dim)
        out(f"  {idx} {cat} {c.question}")
        out(f"        {paint('→', theme.accent)} {c.answer}")
        stats = paint(f"richtig: {c.correct_count}  ·  falsch: {c.wrong_count}", theme.dim)
        out(f"        {stats}")
        out("")
        shown += 1
    if shown == 0:
        _hint(f"(Keine Karten in Kategorie '{filter_cat}'.)", theme, out)


def _ask_index(deck: Deck, inp: InputFn, out: OutputFn, theme: Theme) -> int | None:
    if len(deck) == 0:
        _hint("(Keine Karten vorhanden.)", theme, out)
        return None
    raw = _prompt(inp, f"Index (0..{len(deck) - 1}): ", theme).strip()
    try:
        idx = int(raw)
    except ValueError:
        out(paint("  ✗ Bitte eine ganze Zahl eingeben.", theme.accent))
        return None
    if not 0 <= idx < len(deck):
        out(paint("  ✗ Index außerhalb des Decks.", theme.accent))
        return None
    return idx


def _action_edit(deck: Deck, inp: InputFn, out: OutputFn, theme: Theme) -> None:
    out(_title_line("KARTE BEARBEITEN", theme))
    idx = _ask_index(deck, inp, out, theme)
    if idx is None:
        return
    current = deck[idx]
    out("")
    _hint(f"Aktuell: {current.question} → {current.answer} ({current.category})", theme, out)
    _hint("(Eingabe leer lassen = unverändert)", theme, out)
    out("")
    q = _prompt(inp, "Neue Frage:     ", theme).strip() or None
    a = _prompt(inp, "Neue Antwort:   ", theme).strip() or None
    c = _prompt(inp, "Neue Kategorie: ", theme).strip() or None
    try:
        deck.update(idx, question=q, answer=a, category=c)
        out(paint("\n  ✓ Karte aktualisiert.", theme.accent))
    except (ValueError, CardNotFoundError) as exc:
        out(paint(f"\n  ✗ Fehler: {exc}", theme.accent))


def _action_remove(deck: Deck, inp: InputFn, out: OutputFn, theme: Theme) -> None:
    out(_title_line("KARTE LÖSCHEN", theme))
    idx = _ask_index(deck, inp, out, theme)
    if idx is None:
        return
    removed = deck.remove(idx)
    out(paint(f"\n  ✓ Karte entfernt: {removed.question}", theme.accent))


def _ask_rating(inp: InputFn, out: OutputFn, theme: Theme) -> bool | str:
    """Fragt die Bewertung ab und akzeptiert nur ja/nein (bzw. Abbruch).

    Rückgabe: ``True`` (richtig), ``False`` (falsch) oder ``"abort"`` (Abbruch).
    Bei ungültiger Eingabe wird so lange neu gefragt, bis eine gültige kommt.
    """
    rating = _prompt(inp, "Richtig? [j/n]    ·    [x] Session beenden » ", theme).strip().lower()
    match rating:
        case "x" | "q" | "quit" | "exit":
            return "abort"
        case "j" | "ja" | "y" | "yes":
            return True
        case "n" | "nein" | "no":
            return False
        case _:
            out(paint("  ✗ Bitte nur mit j (ja) oder n (nein) antworten.", theme.accent))
            return _ask_rating(inp, out, theme)


def _action_train(deck: Deck, inp: InputFn, out: OutputFn, theme: Theme) -> None:
    out(_title_line("LERNSESSION", theme))
    if len(deck) == 0:
        _hint("Deck ist leer. Bitte zuerst Karten hinzufügen.", theme, out)
        return
    raw = _prompt(inp, "Wie viele Karten abfragen? [10]: ", theme).strip() or "10"
    try:
        count = int(raw)
    except ValueError:
        out(paint("  ✗ Bitte eine ganze Zahl eingeben.", theme.accent))
        return
    if count <= 0:
        out(paint("  ✗ Anzahl muss größer als 0 sein.", theme.accent))
        return
    session = Session(deck)
    aborted = False
    for i in range(count):
        card = session.next_card()
        _clear(out)
        _banner(theme, out)
        out(_title_line(f"LERNSESSION  ({i + 1}/{count})", theme))
        out("")
        _hint(f"Kategorie: {card.category}", theme, out)
        out("")
        out(f"  {paint('?', theme.accent, bold=True)}  {card.question}")
        out("")
        first = inp(paint("  [Enter] Antwort anzeigen    ·    [x] Session beenden » ", theme.accent)).strip().lower()
        if first in ("x", "q", "quit", "exit"):
            aborted = True
            break
        out(f"\n  {paint('=', theme.accent, bold=True)}  {card.answer}\n")
        rating = _ask_rating(inp, out, theme)
        if rating == "abort":
            aborted = True
            break
        session.grade(card, correct=rating)
    if aborted:
        out(paint(f"\n  ✓ Session abgebrochen. {session.answered} Karte(n) beantwortet.", theme.accent))
    else:
        out(paint(f"\n  ✓ Session beendet. {session.answered} Karte(n) beantwortet.", theme.accent))


def _section_label(text: str, theme: Theme, out: OutputFn) -> None:
    out(paint("  ▸ " + text, theme.accent, bold=True))


def _stat_box_lines(
    title: str,
    value: str,
    theme: Theme,
    width: int = 24,
    value_color: tuple[int, int, int] | None = None,
) -> list[str]:
    """Eine kleine Kennzahl-Box (Titel oben, große Zahl darunter). Liefert die 5 Zeilen."""
    if value_color is None:
        value_color = theme.fg
    inside = width - 2
    fill = inside - 3 - len(title)
    title_line = (
        paint(TL + H + " ", theme.dim)
        + paint(title, theme.dim)
        + paint(" " + H * fill + TR, theme.dim)
    )
    blank = paint(V, theme.dim) + " " * inside + paint(V, theme.dim)
    value_pad = inside - 3 - len(value)
    value_line = (
        paint(V, theme.dim)
        + "   "
        + paint(value, value_color, bold=True)
        + " " * value_pad
        + paint(V, theme.dim)
    )
    bottom = paint(BL + H * inside + BR, theme.dim)
    return [title_line, blank, value_line, blank, bottom]


def _join_horizontal(groups: list[list[str]], gap: str = "  ") -> list[str]:
    """Setzt mehrere gleich hohe Block-Gruppen nebeneinander."""
    return [gap.join(parts) for parts in zip(*groups)]


def _bar(rate: float, theme: Theme, fill_color: tuple[int, int, int], width: int = 8) -> str:
    rate = max(0.0, min(100.0, rate))
    filled = int(round(rate / 100 * width))
    return paint("█" * filled, fill_color) + paint("░" * (width - filled), theme.dim)


def _card_row(card: Card, theme: Theme, fill_color: tuple[int, int, int]) -> str:
    """Zeile in einer BESTE-/SCHWIERIGSTE-Liste: Frage links, Balken/Quote/Ratio rechts."""
    rate = card.success_rate * 100
    bar = _bar(rate, theme, fill_color, width=8)
    pct = f"{int(round(rate)):>3d}%"
    correct = str(card.correct_count)
    wrong = str(card.wrong_count)
    ratio_plain = f"{correct}/{wrong}"
    ratio_pad = max(0, 5 - len(ratio_plain))
    ratio = (
        " " * ratio_pad
        + paint(correct, theme.fg)
        + paint("/", theme.dim)
        + paint(wrong, theme.dim)
    )
    right_visible = 1 + 8 + 2 + 4 + 2 + 5  # = 22
    inside = WIDTH - 4
    q_max = inside - right_visible
    q = card.question
    if len(q) > q_max:
        q = q[: max(0, q_max - 1)] + "…"
    pad_after_q = q_max - len(q)
    border = paint(V, theme.dim)
    right = " " + bar + "  " + paint(pct, fill_color) + "  " + ratio
    return f"{border} {q}{' ' * pad_after_q}{right} {border}"


def _action_stats(deck: Deck, out: OutputFn, theme: Theme) -> None:
    _section_label("STATISTIK", theme, out)
    out("")

    total = total_cards(deck)
    answers = total_answers(deck)
    rate = overall_success_rate(deck) * 100
    boxes = [
        _stat_box_lines("Karten gesamt",   str(total),      theme, value_color=theme.fg),
        _stat_box_lines("Antworten total", str(answers),    theme, value_color=theme.fg),
        _stat_box_lines("Erfolgsquote",    f"{rate:.0f} %", theme, value_color=theme.accent),
    ]
    for line in _join_horizontal(boxes, gap=" "):
        out("  " + line)

    if answers == 0:
        out("")
        _hint("(Noch keine Antworten — Lernsession starten, um Statistik zu sehen.)", theme, out)
        return

    out("")
    _section_label("BESTE 5", theme, out)
    out(paint(_hline(), theme.dim))
    for card in best_cards(deck, limit=5):
        out(_card_row(card, theme, theme.accent))
    out(paint(_bline(), theme.dim))

    out("")
    _section_label("SCHWIERIGSTE 5", theme, out)
    out(paint(_hline(), theme.dim))
    for card in hardest_cards(deck, limit=5):
        out(_card_row(card, theme, theme.warn))
    out(paint(_bline(), theme.dim))


# ─── Hauptschleife ─────────────────────────────────────────────────────────
def run(
    path: Path = DEFAULT_PATH,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
    key_fn: KeyFn = read_key,
    theme_key: str = DEFAULT_THEME,
) -> int:
    if theme_key not in THEMES:
        theme_key = DEFAULT_THEME
    theme = THEMES[theme_key]
    deck = _load_or_empty(path, theme, output_fn)
    selected = 0
    action: str | None = None

    while True:
        theme = THEMES[theme_key]
        if action is None:
            # Menü zeichnen
            _clear(output_fn)
            _banner(theme, output_fn)
            _statusline(deck, path, "MENU", theme, output_fn)
            output_fn("")
            _print_menu(theme, selected, output_fn)
            output_fn("")
            _hotkey_bar(theme, output_fn, in_menu=True)

            key = key_fn()
            if key in ("up", "k"):
                selected = (selected - 1) % len(MENU_ITEMS)
                continue
            if key in ("down", "j"):
                selected = (selected + 1) % len(MENU_ITEMS)
                continue
            if key in ("q", "esc", "0"):
                action = "quit"
            elif key == "enter":
                action = MENU_ITEMS[selected][0]
            elif key == "t":
                action = "theme"
            elif key in {it[0] for it in MENU_ITEMS}:
                action = key
            else:
                continue  # unbekannte Taste -> ignorieren, Menü bleibt stehen

        if action == "quit":
            try:
                save_deck(deck, path)
                _clear(output_fn)
                _banner(theme, output_fn)
                output_fn(paint(f"  Gespeichert nach {path}.", theme.fg))
                output_fn(paint("  Auf Wiedersehen!\n", theme.accent))
            except OSError as exc:
                output_fn(paint(f"  ✗ Fehler beim Speichern: {exc}", theme.accent))
                return 1
            return 0

        # Aktion ausführen
        _clear(output_fn)
        _banner(theme, output_fn)
        _statusline(deck, path, "ACTION", theme, output_fn)
        output_fn("")

        if action == "1":
            _action_add(deck, input_fn, output_fn, theme)
        elif action == "2":
            _action_list(deck, input_fn, output_fn, theme)
        elif action == "3":
            _action_edit(deck, input_fn, output_fn, theme)
        elif action == "4":
            _action_remove(deck, input_fn, output_fn, theme)
        elif action == "5":
            _action_train(deck, input_fn, output_fn, theme)
        elif action == "6":
            _action_stats(deck, output_fn, theme)
        elif action == "theme":
            theme_key = _action_theme(theme_key, input_fn, output_fn)

        try:
            save_deck(deck, path)
        except OSError as exc:
            output_fn(paint(f"  Warnung: Zwischenspeichern fehlgeschlagen: {exc}", theme.dim))

        _pause(key_fn, theme, output_fn)
        action = None


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        prog="lernkarten",
        description="Interaktiver Lernkarten-Trainer (Menü im Terminal).",
    )
    parser.add_argument(
        "--file",
        default=str(DEFAULT_PATH),
        help=f"Pfad zur JSON-Datei (Standard: {DEFAULT_PATH}).",
    )
    parser.add_argument(
        "--theme",
        default=DEFAULT_THEME,
        choices=list(THEMES.keys()),
        help="Farb-Theme der Oberfläche.",
    )
    args = parser.parse_args(argv)
    # ANSI-Escape-Codes unter Windows aktivieren.
    if os.name == "nt":  # pragma: no cover
        os.system("")
    return run(Path(args.file), theme_key=args.theme)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
