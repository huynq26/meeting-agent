# Meeting Agent

The project provides a real-time English communication copilot for Zoom-style meetings. The goal is not to alter a speaker's voice; it provides private wording suggestions that help a speaker sound clearer, more natural, and more professional while the meeting continues.

## Phase 1 MVP: English wording copilot

The MVP receives short transcript segments from a meeting stream and returns private coaching suggestions. It is designed to sit behind a Zoom Realtime Media Streams, caption, or local transcription integration.

### Capabilities

- Detect common filler phrases and suggest concise alternatives.
- Convert overly casual meeting language into more professional wording.
- Suggest clearer versions of tentative or indirect statements.
- Keep the original transcript segment available for auditability.

### Non-goals for Phase 1

- No live accent conversion or voice replacement.
- No automatic message sending to other meeting participants.
- No storage of meeting transcripts by default.

## Local usage

Run the command-line prototype with a transcript segment:

```bash
PYTHONPATH=src python -m meeting_agent.english_copilot "I just wanna ask if you can maybe send the report asap."
```

Expected output:

```text
Original: I just wanna ask if you can maybe send the report asap.
Suggestion: I would like to ask if you can maybe send the report as soon as possible.
Notes:
- Replace casual wording with a more professional phrase.
- Use a clearer phrase for urgency.
```

## Integration shape

A production Zoom integration can pass partial or finalized transcript segments into `suggest_wording`. The response can be rendered in a private web panel, desktop overlay, or companion mobile view so only the speaker sees the coaching.

## Phase 2: real-time transcript sessions

Phase 2 adds `RealtimeCopilot`, a provider-neutral session adapter for streams
that revise partial transcripts before finalizing them. It:

- numbers meaningful revisions so clients can replace stale suggestions;
- suppresses identical partial updates and late retries;
- emits a final event even when the final text matches the latest partial; and
- discards completed transcript text rather than building a transcript history.

```python
from meeting_agent.realtime_copilot import RealtimeCopilot, TranscriptUpdate

copilot = RealtimeCopilot()
event = copilot.process(TranscriptUpdate("utterance-42", "I wanna help"))
if event is not None:
    print(event.revision, event.wording.suggestion)

copilot.process(
    TranscriptUpdate("utterance-42", "I wanna help with that.", is_final=True)
)
copilot.reset()  # clear session metadata when the meeting ends
```
