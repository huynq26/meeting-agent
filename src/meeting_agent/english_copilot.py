"""Phase 1 English wording copilot prototype.

This module intentionally uses deterministic rules so the first MVP can be
run, tested, and demonstrated without external AI service credentials. A
production system can replace the rule engine with an LLM while preserving the
same request/response shape.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import sys


@dataclass(frozen=True)
class WordingSuggestion:
    """Private wording suggestion for one transcript segment."""

    original: str
    suggestion: str
    notes: tuple[str, ...]


_REPLACEMENTS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (
        re.compile(r"\bI just wanna\b", re.IGNORECASE),
        "I would like to",
        "Replace casual wording with a more professional phrase.",
    ),
    (
        re.compile(r"\bwanna\b", re.IGNORECASE),
        "want to",
        "Expand casual contractions for clearer business English.",
    ),
    (
        re.compile(r"\bgonna\b", re.IGNORECASE),
        "going to",
        "Expand casual contractions for clearer business English.",
    ),
    (
        re.compile(r"\basap\b", re.IGNORECASE),
        "as soon as possible",
        "Use a clearer phrase for urgency.",
    ),
    (
        re.compile(r"^maybe we can\b", re.IGNORECASE),
        "I suggest we",
        "Make tentative language more direct.",
    ),
    (
        re.compile(r"\bI think we should maybe\b", re.IGNORECASE),
        "I recommend that we",
        "Turn a hesitant phrase into a confident recommendation.",
    ),
    (
        re.compile(
            r"\bkind of\b(?=\s+(?:unclear|confusing|difficult|hard|"
            r"concerned|worried|unsure|hesitant|late|slow)\b)",
            re.IGNORECASE,
        ),
        "somewhat",
        "Replace filler wording with a more precise word.",
    ),
    (
        re.compile(
            r"\bsort of\b(?=\s+(?:unclear|confusing|difficult|hard|"
            r"concerned|worried|unsure|hesitant|late|slow)\b)",
            re.IGNORECASE,
        ),
        "somewhat",
        "Replace filler wording with a more precise word.",
    ),
)


def suggest_wording(transcript_segment: str) -> WordingSuggestion:
    """Return a private wording suggestion for a transcript segment.

    The function accepts one short finalized or partial transcript segment from
    a meeting stream. It returns the original text, a suggested rewrite, and a
    list of coaching notes that can be displayed privately to the speaker.
    """

    original = transcript_segment.strip()
    suggestion = original
    notes: list[str] = []

    for pattern, replacement, note in _REPLACEMENTS:
        suggestion, count = pattern.subn(replacement, suggestion)
        if count and note not in notes:
            notes.append(note)

    normalized_suggestion = _normalize_spacing(suggestion)
    if normalized_suggestion != suggestion:
        notes.append("Normalize repeated whitespace for readability.")
    suggestion = normalized_suggestion

    if suggestion == original:
        notes = ["No wording changes suggested for this segment."]

    return WordingSuggestion(
        original=original,
        suggestion=suggestion,
        notes=tuple(notes),
    )


def _normalize_spacing(value: str) -> str:
    """Normalize repeated whitespace in the suggested wording."""

    return re.sub(r"\s+", " ", value).strip()


def main(argv: list[str] | None = None) -> int:
    """Run the command-line prototype."""

    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Usage: python -m meeting_agent.english_copilot '<transcript segment>'")
        return 2

    result = suggest_wording(" ".join(args))
    print(f"Original: {result.original}")
    print(f"Suggestion: {result.suggestion}")
    print("Notes:")
    for note in result.notes:
        print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
