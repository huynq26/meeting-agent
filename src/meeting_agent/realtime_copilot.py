"""Session-aware adapter for real-time meeting transcript updates.

Transcription providers commonly send several revisions of the same utterance
before marking it final.  ``RealtimeCopilot`` turns that stream into a clean
sequence of private coaching events without repeatedly rendering duplicates.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from meeting_agent.english_copilot import WordingSuggestion, suggest_wording


@dataclass(frozen=True)
class TranscriptUpdate:
    """One partial or final update emitted by a transcription provider."""

    segment_id: str
    text: str
    is_final: bool = False


@dataclass(frozen=True)
class CoachingEvent:
    """A suggestion ready to render in the speaker's private UI."""

    segment_id: str
    revision: int
    is_final: bool
    wording: WordingSuggestion


class RealtimeCopilot:
    """Process transcript revisions while retaining only active utterances.

    Completed transcript text is discarded as soon as a segment is finalized.
    A bounded collection of recently finalized IDs is retained so late provider
    retries can be ignored without allowing session metadata to grow forever.
    Call ``reset`` at the end of a meeting to clear all session state.
    """

    def __init__(self, finalized_capacity: int = 1024) -> None:
        if finalized_capacity < 1:
            raise ValueError("finalized_capacity must be at least 1")
        self._finalized_capacity = finalized_capacity
        self._active: dict[str, tuple[str, int]] = {}
        self._finalized: OrderedDict[str, None] = OrderedDict()

    def process(self, update: TranscriptUpdate) -> CoachingEvent | None:
        """Return a coaching event, or ``None`` for duplicate/late updates."""

        segment_id = update.segment_id.strip()
        if not segment_id:
            raise ValueError("segment_id must not be blank")
        if segment_id in self._finalized:
            return None

        text = update.text.strip()
        previous = self._active.get(segment_id)
        if previous is not None and previous[0] == text:
            if update.is_final:
                self._active.pop(segment_id)
                self._remember_finalized(segment_id)
                return CoachingEvent(
                    segment_id=segment_id,
                    revision=previous[1],
                    is_final=True,
                    wording=suggest_wording(text),
                )
            return None

        revision = 1 if previous is None else previous[1] + 1
        if update.is_final:
            self._active.pop(segment_id, None)
            self._remember_finalized(segment_id)
        else:
            self._active[segment_id] = (text, revision)

        return CoachingEvent(
            segment_id=segment_id,
            revision=revision,
            is_final=update.is_final,
            wording=suggest_wording(text),
        )

    def _remember_finalized(self, segment_id: str) -> None:
        """Retain an ID only for the configured recent-retry window."""

        self._finalized[segment_id] = None
        self._finalized.move_to_end(segment_id)
        if len(self._finalized) > self._finalized_capacity:
            self._finalized.popitem(last=False)

    def reset(self) -> None:
        """Forget all state associated with the current meeting."""

        self._active.clear()
        self._finalized.clear()
