import asyncio
import sqlite3

from sensing import sensing_server
from sensing.screen import Screen
from sensing.sensing_server import CapturePauseRequest
from sensing.streamer import Streamer


def test_capture_pause_drops_stale_screen_and_streamer_state(tmp_path, monkeypatch):
    db_path = tmp_path / "actions.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE observations (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO observations (id) VALUES (7)")

    screen = Screen.__new__(Screen)
    screen._capture_paused = False
    screen._pending_event = {"eid": 1}
    screen._debounce_handle = None
    screen._frames = {1: "stale frame"}
    screen._frame_lock = asyncio.Lock()
    screen._key_activity_start = 1.0
    screen._key_screenshots = ["stale.jpg"]
    screen._background_tasks = set()
    streamer = Streamer(db_path=str(db_path), screenshot_dir=str(tmp_path))
    streamer._stored_actions = [{"action": "stale"}]
    streamer._last_processed_id = 3
    streamer._last_processed_id_tmp = 4
    progress = type(
        "Progress",
        (),
        {"reset_cooldown": lambda self: None, "reset_timing": lambda self: None},
    )()
    monkeypatch.setattr(sensing_server, "screen", screen)
    monkeypatch.setattr(sensing_server, "streamer", streamer)
    monkeypatch.setattr(sensing_server, "progress_detector", progress)

    paused = asyncio.run(
        sensing_server.set_capture_pause(CapturePauseRequest(paused=True))
    )
    resumed = asyncio.run(
        sensing_server.set_capture_pause(CapturePauseRequest(paused=False))
    )

    assert paused.status == "paused"
    assert resumed.status == "ok"
    assert screen._capture_paused is False
    assert screen._pending_event is None
    assert screen._frames == {}
    assert screen._key_screenshots == []
    assert streamer._stored_actions == []
    assert streamer._last_processed_id == streamer._last_processed_id_tmp == 7
