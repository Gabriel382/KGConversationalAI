from kgconvai.state import DialogueSession, Speaker, Turn


def test_session_starts_at_start_with_empty_history():
    s = DialogueSession()
    assert s.current_state == "start"
    assert s.history == []
    assert not s.is_finished()


def test_session_add_turns_records_speakers_in_order():
    s = DialogueSession()
    s.add_user_turn("hello")
    s.add_agent_turn("hi")
    s.add_user_turn("bye")
    assert s.history == [
        Turn(Speaker.USER, "hello"),
        Turn(Speaker.AGENT, "hi"),
        Turn(Speaker.USER, "bye"),
    ]


def test_session_recent_returns_tail():
    s = DialogueSession()
    for i in range(10):
        s.add_user_turn(f"u{i}")
    assert [t.text for t in s.recent(3)] == ["u7", "u8", "u9"]


def test_session_is_finished_when_state_is_end():
    s = DialogueSession()
    s.current_state = "end"
    assert s.is_finished()
