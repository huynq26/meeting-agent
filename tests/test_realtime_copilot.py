import pytest

from meeting_agent.realtime_copilot import RealtimeCopilot, TranscriptUpdate


def test_emits_numbered_events_for_revised_partial_transcripts() -> None:
    copilot = RealtimeCopilot()

    first = copilot.process(TranscriptUpdate("segment-1", "I wanna", 1))
    second = copilot.process(TranscriptUpdate("segment-1", "I wanna help", 2))

    assert first is not None
    assert first.revision == 1
    assert first.wording.suggestion == "I want to"
    assert second is not None
    assert second.revision == 2
    assert second.wording.suggestion == "I want to help"


def test_suppresses_duplicate_partial_transcripts() -> None:
    copilot = RealtimeCopilot()
    assert copilot.process(TranscriptUpdate("segment-1", "Could you clarify?", 1))
    duplicate = copilot.process(TranscriptUpdate("segment-1", "Could you clarify?", 2))
    assert duplicate is None


def test_emits_final_state_for_unchanged_partial_then_ignores_late_updates() -> None:
    copilot = RealtimeCopilot()
    copilot.process(TranscriptUpdate("segment-1", "Please send it asap.", 1))

    final = copilot.process(
        TranscriptUpdate("segment-1", "Please send it asap.", 2, is_final=True)
    )

    assert final is not None
    assert final.revision == 1
    assert final.is_final is True
    assert final.wording.suggestion == "Please send it as soon as possible."
    assert copilot.process(TranscriptUpdate("segment-1", "late retry", 3)) is None


def test_changed_final_transcript_receives_next_revision() -> None:
    copilot = RealtimeCopilot()
    copilot.process(TranscriptUpdate("segment-1", "Maybe we", 1))

    final = copilot.process(
        TranscriptUpdate("segment-1", "Maybe we can wait.", 2, is_final=True)
    )

    assert final is not None
    assert final.revision == 2
    assert final.wording.suggestion == "I suggest we wait."


def test_reset_allows_segment_ids_to_be_reused_in_a_new_meeting() -> None:
    copilot = RealtimeCopilot()
    copilot.process(TranscriptUpdate("segment-1", "Done", 1, is_final=True))

    copilot.reset()

    event = copilot.process(TranscriptUpdate("segment-1", "New meeting", 1))
    assert event is not None
    assert event.revision == 1


def test_evicts_old_tombstones_but_suppresses_recent_retries() -> None:
    copilot = RealtimeCopilot(finalized_capacity=2)
    copilot.process(TranscriptUpdate("segment-1", "First", 1, is_final=True))
    copilot.process(TranscriptUpdate("segment-2", "Second", 1, is_final=True))

    assert copilot.process(TranscriptUpdate("segment-2", "retry", 2)) is None

    copilot.process(TranscriptUpdate("segment-3", "Third", 1, is_final=True))

    old_segment = copilot.process(TranscriptUpdate("segment-1", "Reused", 2))
    assert old_segment is not None
    assert old_segment.revision == 1
    assert copilot.process(TranscriptUpdate("segment-3", "retry", 2)) is None


def test_rejects_out_of_order_partial_retry() -> None:
    copilot = RealtimeCopilot()
    copilot.process(TranscriptUpdate("segment-1", "I wanna", 10))
    current = copilot.process(TranscriptUpdate("segment-1", "I wanna help", 12))

    stale = copilot.process(TranscriptUpdate("segment-1", "I wanna", 11))

    assert current is not None
    assert current.revision == 2
    assert stale is None


def test_evicts_abandoned_active_segments() -> None:
    copilot = RealtimeCopilot(active_capacity=2)
    copilot.process(TranscriptUpdate("segment-1", "First", 1))
    copilot.process(TranscriptUpdate("segment-2", "Second", 1))
    copilot.process(TranscriptUpdate("segment-3", "Third", 1))

    stale = copilot.process(TranscriptUpdate("segment-1", "Stale first", 1))
    evicted = copilot.process(TranscriptUpdate("segment-1", "First again", 2))
    retained = copilot.process(TranscriptUpdate("segment-3", "Third again", 2))

    assert stale is None
    assert evicted is not None
    assert evicted.revision == 2
    assert retained is not None
    assert retained.revision == 2


def test_bounds_evicted_segment_ordering_metadata() -> None:
    copilot = RealtimeCopilot(active_capacity=1, ordering_capacity=1)
    copilot.process(TranscriptUpdate("segment-1", "First", 1))
    copilot.process(TranscriptUpdate("segment-2", "Second", 1))
    copilot.process(TranscriptUpdate("segment-3", "Third", 1))

    retained_retry = copilot.process(TranscriptUpdate("segment-2", "Stale", 1))
    expired_retry = copilot.process(TranscriptUpdate("segment-1", "Expired", 1))

    assert retained_retry is None
    assert expired_retry is not None
    assert expired_retry.revision == 1


def test_rejects_non_positive_finalized_capacity() -> None:
    with pytest.raises(ValueError, match="finalized_capacity must be at least 1"):
        RealtimeCopilot(finalized_capacity=0)


def test_rejects_non_positive_active_capacity() -> None:
    with pytest.raises(ValueError, match="active_capacity must be at least 1"):
        RealtimeCopilot(active_capacity=0)


def test_rejects_non_positive_ordering_capacity() -> None:
    with pytest.raises(ValueError, match="ordering_capacity must be at least 1"):
        RealtimeCopilot(ordering_capacity=0)


def test_rejects_negative_sequence() -> None:
    with pytest.raises(ValueError, match="sequence must not be negative"):
        RealtimeCopilot().process(TranscriptUpdate("segment-1", "Hello", -1))


def test_rejects_blank_segment_id() -> None:
    with pytest.raises(ValueError, match="segment_id must not be blank"):
        RealtimeCopilot().process(TranscriptUpdate("  ", "Hello", 1))
