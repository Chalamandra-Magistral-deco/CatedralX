import copy

import pytest

from elite.MSX.provenance import (
    aggregate_cycle,
    build_provenance,
    verify_provenance,
)


def _record(inputs=None):
    original = {"market": {"price": 101.25}} if inputs is None else inputs
    record = build_provenance(
        "market_observation",
        "PERCEIVE.sensors",
        "v1",
        original,
        output={"accepted": True},
        vector="RSX",
        parent="cycle-001",
        timestamp=1_800_000_000,
    )
    return record, original


def test_verify_provenance_matches_original_inputs_and_record():
    record, original = _record()

    assert verify_provenance(record, original) is True


def test_verify_provenance_rejects_different_original_inputs():
    record, _ = _record()

    assert verify_provenance(record, {"market": {"price": 999.0}}) is False


def test_verify_provenance_rejects_record_field_tampering():
    record, original = _record()
    tampered = copy.deepcopy(record)
    tampered["output"]["accepted"] = False

    assert verify_provenance(tampered, original) is False


def test_verify_provenance_rejects_input_hash_tampering():
    record, original = _record()
    tampered = copy.deepcopy(record)
    tampered["input_hash"] = "0" * 64

    assert verify_provenance(tampered, original) is False


def test_aggregate_cycle_verifies_all_original_inputs_and_seals_manifest():
    first, first_inputs = _record({"price": 101.25})
    second_inputs = {"decision": "hold", "reason": "insufficient evidence"}
    second = build_provenance(
        "decision_review",
        "REASON.review",
        "v1",
        second_inputs,
        vector="SCX",
        parent="cycle-001",
        timestamp=1_800_000_001,
    )

    manifest = aggregate_cycle(
        "cycle-001",
        [first, second],
        original_inputs={
            first["id"]: first_inputs,
            second["id"]: second_inputs,
        },
    )

    assert manifest["integrity_status"] == "verified"
    assert manifest["record_count"] == 2
    assert len(manifest["cycle_hash"]) == 64
    assert manifest["record_ids"] == [first["id"], second["id"]]


def test_aggregate_cycle_rejects_tampered_record():
    record, original = _record()
    tampered = copy.deepcopy(record)
    tampered["status"] = "approved"

    with pytest.raises(ValueError, match="integridad de provenance inválida"):
        aggregate_cycle(
            "cycle-001",
            [tampered],
            original_inputs={record["id"]: original},
        )


def test_aggregate_cycle_rejects_missing_original_input():
    record, _ = _record()

    with pytest.raises(ValueError, match="faltan entradas originales"):
        aggregate_cycle("cycle-001", [record], original_inputs={})


def test_aggregate_cycle_rejects_extra_original_input():
    record, original = _record()

    with pytest.raises(ValueError, match="IDs que no pertenecen"):
        aggregate_cycle(
            "cycle-001",
            [record],
            original_inputs={
                record["id"]: original,
                "unrelated": {"x": 1},
            },
        )


def test_build_provenance_rejects_non_finite_input():
    with pytest.raises(ValueError):
        build_provenance(
            "invalid",
            "module",
            "v1",
            {"value": float("nan")},
        )
