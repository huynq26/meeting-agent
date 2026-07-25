"""Session-aware adapter for real-time meeting transcript updates.

Transcription providers commonly send several revisions of the same utterance
before marking it final.  ``RealtimeCopilot`` turns that stream into a clean
sequence of private coaching events without repeatedly rendering duplicates.
"""

from __future__ import annotations

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
    Finalized IDs are retained so late provider retries can be ignored; call
    ``reset`` at the end of a meeting to clear all session state.
    """

    def __init__(self) -> None:
        self._active: dict[str, tuple[str, int]] = {}
        self._finalized: set[str] = set()

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
                self._finalized.add(segment_id)
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
            self._finalized.add(segment_id)
        else:
            self._active[segment_id] = (text, revision)

        return CoachingEvent(
            segment_id=segment_id,
            revision=revision,
            is_final=update.is_final,
            wording=suggest_wording(text),
        )

    def reset(self) -> None:
        """Forget all state associated with the current meeting."""

        self._active.clear()
        self._finalized.clear()
