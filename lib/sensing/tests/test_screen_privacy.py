from sensing import screen


def test_capture_blocklist_matches_only_frontmost_app_or_window_title(monkeypatch):
    monkeypatch.setattr(
        screen,
        "_get_visible_windows",
        lambda: [
            (
                {
                    "kCGWindowOwnerName": "Google Chrome",
                    "kCGWindowName": "Quarterly Payroll",
                },
                1.0,
            ),
            (
                {
                    "kCGWindowOwnerName": "1Password",
                    "kCGWindowName": "Vault",
                },
                0.5,
            ),
        ],
    )

    assert screen._frontmost_window_matches(["chrome"])
    assert screen._frontmost_window_matches(["payroll"])
    assert not screen._frontmost_window_matches(["1password"])
    assert not screen._frontmost_window_matches([])
