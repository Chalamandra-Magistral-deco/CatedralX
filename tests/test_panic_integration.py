"""Integration tests for emergency-lock enforcement in the analysis daemon."""

from PERCEIVE import bunker
from DSX.DEFENSE import defense


def test_active_panic_marker_prevents_bunker_cycle_before_snapshot_io(tmp_path, monkeypatch):
    marker = tmp_path / ".panic"
    marker.write_text("test emergency lock", encoding="utf-8")
    monkeypatch.setattr(defense, "PATH_PANIC", marker)

    def forbidden_read():
        raise AssertionError("Snapshot must not be read while panic lock is active")

    monkeypatch.setattr(bunker.BunkerDaemon, "_leer_snapshot", staticmethod(forbidden_read))
    monkeypatch.setattr(
        bunker,
        "execute_cycle",
        lambda _sensory: (_ for _ in ()).throw(
            AssertionError("Reasoning cycle must not run while panic lock is active")
        ),
    )

    daemon = object.__new__(bunker.BunkerDaemon)
    assert daemon._ciclo() is None


def test_bunker_cycle_is_not_blocked_by_nonexistent_marker(tmp_path, monkeypatch):
    marker = tmp_path / ".panic"
    monkeypatch.setattr(defense, "PATH_PANIC", marker)
    # Without a marker, normal operation continues to the snapshot lookup. An
    # empty snapshot returns None and must not trigger the reasoning engine.
    monkeypatch.setattr(bunker.BunkerDaemon, "_leer_snapshot", staticmethod(lambda: {}))
    monkeypatch.setattr(
        bunker,
        "execute_cycle",
        lambda _sensory: (_ for _ in ()).throw(
            AssertionError("No reasoning should run without a snapshot")
        ),
    )
    daemon = object.__new__(bunker.BunkerDaemon)
    assert daemon._ciclo() is None


def test_one_shot_entrypoint_refuses_cycle_when_panic_marker_active(tmp_path, monkeypatch, capsys):
    import json
    from REASON import razon

    marker = tmp_path / ".panic"
    marker.write_text("test emergency lock", encoding="utf-8")
    monkeypatch.setattr(defense, "PATH_PANIC", marker)
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_PATH", str(tmp_path / "must-not-read.json"))
    monkeypatch.setattr(
        razon,
        "execute_cycle",
        lambda _sensory: (_ for _ in ()).throw(
            AssertionError("Reasoning must not run when panic lock is active")
        ),
    )
    monkeypatch.setattr(
        razon,
        "registrar_prediccion",
        lambda _result: (_ for _ in ()).throw(
            AssertionError("Blocked cycle must not record a prediction")
        ),
    )

    assert razon.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "NO_CYCLE"
    assert "Bloqueo de emergencia activo" in result["reason"]
    assert result["trading_enabled"] is False
    assert result["orders_created"] is False
    assert result["orders_executed"] is False
