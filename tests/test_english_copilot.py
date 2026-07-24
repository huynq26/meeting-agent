from meeting_agent.english_copilot import suggest_wording


def test_suggest_wording_rewrites_casual_urgent_request() -> None:
    result = suggest_wording("I just wanna ask if you can send it asap.")

    assert result.original == "I just wanna ask if you can send it asap."
    assert result.suggestion == (
        "I would like to ask if you can send it as soon as possible."
    )
    assert "Replace casual wording with a more professional phrase." in result.notes
    assert "Use a clearer phrase for urgency." in result.notes


def test_suggest_wording_returns_no_change_note() -> None:
    result = suggest_wording("Could you clarify the project timeline?")

    assert result.suggestion == "Could you clarify the project timeline?"
    assert result.notes == ("No wording changes suggested for this segment.",)
