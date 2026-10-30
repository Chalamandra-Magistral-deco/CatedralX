"""Tests for user-facing feedback capture, traceability and safe aggregation."""
import json
from pathlib import Path

import pytest
from FEX.FEEDBACK.user_feedback import record_user_feedback, summarize_user_feedback


def _feedback(**overrides):
    data = {
        "result_id": "result-123",
        "cycle_id": "cycle-456",
        "rating": 4,
        "assessment": "useful",
        "reason_code": "clarity",
        "preferred_next_step": "explain",
        "correction": None,
    }
    data.update(overrides)
    return data


def test_records_user_feedback_append_only_with_trace_and_clear_ack(tmp_path):
    path = tmp_path / "feedback" / "user-feedback.jsonl"
    result = record_user_feedback(_feedback(), path=path)
    assert result["status"] == "FEEDBACK_RECORDED_FOR_REVIEW"
    assert result["policy_changed"] is False
    assert result["automatic_retraining"] is False
    record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert record["record_type"] == "user_feedback"
    assert record["result_id"] == "result-123"
    assert record["cycle_id"] == "cycle-456"
    assert record["rating"] == 4
    assert record["controls"]["append_only"] is True
    assert record["controls"]["orders_executed"] is False
    assert "user_id" not in record
    assert "email" not in record


def test_requires_link_and_strict_integer_rating(tmp_path):
    with pytest.raises(ValueError, match="result_id o cycle_id"):
        record_user_feedback(_feedback(result_id=None, cycle_id=None), path=tmp_path / "f.jsonl")
    for index, rating in enumerate((True, 0, 6, 4.0, None)):
        with pytest.raises(ValueError, match="rating"):
            record_user_feedback(_feedback(rating=rating), path=tmp_path / f"{index}.jsonl")


def test_rejects_unexpected_fields_to_avoid_accidental_data_collection(tmp_path):
    with pytest.raises(ValueError, match="Campos no permitidos"):
        record_user_feedback(
            _feedback(user_email="someone@example.invalid"),
            path=tmp_path / "feedback.jsonl",
        )


def test_validates_correction_length_and_enums(tmp_path):
    with pytest.raises(ValueError, match="1000 caracteres"):
        record_user_feedback(_feedback(correction="x" * 1001), path=tmp_path / "long.jsonl")
    with pytest.raises(ValueError, match="assessment"):
        record_user_feedback(_feedback(assessment="maybe"), path=tmp_path / "enum.jsonl")


def test_summary_waits_for_sample_then_recommends_review_without_auto_change(tmp_path):
    path = tmp_path / "feedback.jsonl"
    first = record_user_feedback(_feedback(), path=path)
    early = summarize_user_feedback(path)
    assert early["feedback_count"] == 1
    assert early["recommended_actions"] == ["COLLECT_MORE_FEEDBACK_BEFORE_GENERALIZING"]
    assert early["automatic_policy_changes"] is False

    for index in range(4):
        record_user_feedback(
            _feedback(
                result_id=f"result-{index + 2}",
                cycle_id=f"cycle-{index + 2}",
                rating=1,
                assessment="incorrect",
                reason_code="correctness",
                preferred_next_step="human_review",
            ),
            path=path,
        )
    report = summarize_user_feedback(path)
    assert report["feedback_count"] == 5
    assert report["average_rating"] == 1.6
    assert report["review_required"] is True
    assert "VERIFY_CORRECTNESS_AND_EVIDENCE_PATH" in report["recommended_actions"]
    assert report["automatic_policy_changes"] is False
    assert report["automatic_retraining"] is False
    assert first["feedback_id"]


def test_report_fails_closed_on_corrupt_ledger(tmp_path):
    path = tmp_path / "feedback.jsonl"
    path.write_text("{invalid json}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="línea 1"):
        summarize_user_feedback(path)


def test_feedback_ledger_must_live_outside_repository(tmp_path):
    from FEX.FEEDBACK import user_feedback

    repo_root = Path(user_feedback.__file__).resolve().parents[3]
    with pytest.raises(ValueError, match="fuera del repositorio"):
        user_feedback.record_user_feedback(
            _feedback(), path=repo_root / "unsafe-feedback.jsonl"
        )



def test_new_ledger_file_has_private_permissions(tmp_path):
    import stat

    path = tmp_path / "private.jsonl"
    record_user_feedback(_feedback(), path=path)
    assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0


def test_configured_path_is_used_when_no_explicit_path_is_passed(tmp_path, monkeypatch):
    from FEX.FEEDBACK.user_feedback import user_feedback_path

    configured = tmp_path / "configured" / "user-feedback.jsonl"
    monkeypatch.setenv("CATEDRALX_USER_FEEDBACK_PATH", str(configured))
    assert user_feedback_path() == configured.resolve()
    result = record_user_feedback(_feedback(), path=None)
    assert result["status"] == "FEEDBACK_RECORDED_FOR_REVIEW"
    assert configured.exists()
