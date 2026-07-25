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


def test_suggest_wording_reports_whitespace_normalization_as_change() -> None:
    result = suggest_wording("Could  you clarify?")

    assert result.original == "Could  you clarify?"
    assert result.suggestion == "Could you clarify?"
    assert result.notes == ("Normalize repeated whitespace for readability.",)


def test_suggest_wording_rewrites_maybe_we_can_as_standalone_clause() -> None:
    result = suggest_wording("Maybe we can delay the release.")

    assert result.suggestion == "I suggest we delay the release."
    assert result.notes == ("Make tentative language more direct.",)


def test_suggest_wording_preserves_maybe_we_can_in_embedded_question() -> None:
    result = suggest_wording("Do you think maybe we can delay the release?")

    assert result.suggestion == "Do you think maybe we can delay the release?"
    assert result.notes == ("No wording changes suggested for this segment.",)


def test_suggest_wording_rewrites_kind_of_when_used_as_filler() -> None:
    result = suggest_wording("The project timeline is kind of unclear.")

    assert result.suggestion == "The project timeline is somewhat unclear."
    assert result.notes == ("Replace filler wording with a more precise word.",)


def test_suggest_wording_preserves_kind_of_in_noun_question() -> None:
    result = suggest_wording("What kind of support do you need?")

    assert result.suggestion == "What kind of support do you need?"
    assert result.notes == ("No wording changes suggested for this segment.",)


def test_suggest_wording_distinguishes_sort_of_filler_from_noun_phrase() -> None:
    filler = suggest_wording("I am sort of worried about the deadline.")
    noun_phrase = suggest_wording("What sort of access should we provide?")

    assert filler.suggestion == "I am somewhat worried about the deadline."
    assert noun_phrase.suggestion == "What sort of access should we provide?"
