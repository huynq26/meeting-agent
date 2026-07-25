import pytest

from meeting_agent.realtime_copilot import RealtimeCopilot, TranscriptUpdate


def test_emits_numbered_events_for_revised_partial_transcripts() -> None:
    copilot = RealtimeCopilot()

    first = copilot.process(TranscriptUpdate("segment-1", "I wanna"))
    second = copilot.process(TranscriptUpdate("segment-1", "I wanna help"))

    assert first is not None
    assert first.revision == 1
    assert first.wording.suggestion == "I want to"
    assert second is not None
    assert second.revision == 2
    assert second.wording.suggestion == "I want to help"


def test_suppresses_duplicate_partial_transcripts() -> None:
    copilot = RealtimeCopilot()
    update = TranscriptUpdate("segment-1", "Could you clarify?")

    assert copilot.process(update) is not None
    assert copilot.process(update) is None


def test_emits_final_state_for_unchanged_partial_then_ignores_late_updates() -> None:
    copilot = RealtimeCopilot()
    copilot.process(TranscriptUpdate("segment-1", "Please send it asap."))

    final = copilot.process(
        TranscriptUpdate("segment-1", "Please send it asap.", is_final=True)
    )

    assert final is not None
    assert final.revision == 1
    assert final.is_final is True
    assert final.wording.suggestion == "Please send it as soon as possible."
    assert copilot.process(TranscriptUpdate("segment-1", "late retry")) is None


def test_changed_final_transcript_receives_next_revision() -> None:
    copilot = RealtimeCopilot()
    copilot.process(TranscriptUpdate("segment-1", "Maybe we"))

    final = copilot.process(
        TranscriptUpdate("segment-1", "Maybe we can wait.", is_final=True)
    )

    assert final is not None
    assert final.revision == 2
    assert final.wording.suggestion == "I suggest we wait."


def test_reset_allows_segment_ids_to_be_reused_in_a_new_meeting() -> None:
    copilot = RealtimeCopilot()
    copilot.process(TranscriptUpdate("segment-1", "Done", is_final=True))

    copilot.reset()

    event = copilot.process(TranscriptUpdate("segment-1", "New meeting"))
    assert event is not None
    assert event.revision == 1


def test_rejects_blank_segment_id() -> None:
    with pytest.raises(ValueError, match="segment_id must not be blank"):
        RealtimeCopilot().process(TranscriptUpdate("  ", "Hello"))
