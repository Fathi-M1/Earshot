import time

from earshot import sessions


def test_sessions_save_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("EARSHOT_SESSIONS_DB", str(tmp_path / "sessions.db"))
    sessions.reset_connection()
    now = time.time()
    sessions.add_event("line", "the quiz starts now", ts=now, topic="quiz")
    sessions.add_event("alert", "Fathi, the quiz is Monday", ts=now + 60, topic="quiz")
    sessions.add_event("catchup", "Quiz Monday", ts=now + 120)
    listed = sessions.list_saved()
    assert len(listed) == 1
    assert "quiz" in listed[0]["label"]
    assert listed[0]["lines"] == 1
    assert listed[0]["start"] and listed[0]["end"]
    detail = sessions.get_session(listed[0]["id"])
    assert [e["kind"] for e in detail["events"]] == ["line", "alert", "catchup"]
    sessions.wipe()
    assert sessions.list_saved() == []
    sessions.reset_connection()
