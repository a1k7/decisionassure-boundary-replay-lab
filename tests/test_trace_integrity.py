"""Trace integrity tests.

Prove:
  - A correctly built trace verifies.
  - Tampering with a hashed field is detected.
  - Missing required fields cause verification failure.
  - Reordering JSON object keys does not change the canonical hash.
"""

from __future__ import annotations

import copy
import json

from src.execution_authority import evaluate as eval_exec
from src.impact_analysis import analyze
from src.replay_engine import run_original, run_replay
from src.trace_builder import build_trace
from src.trace_integrity import (
    HASHED_TOP_LEVEL_FIELDS,
    canonical_dumps,
    compute_trace_hash,
    verify_trace,
)


def _build(scenario, trace_id: str = "t-1"):
    original = run_original(scenario)
    replay = run_replay(scenario)
    impact = analyze(original, replay)
    exec_result = eval_exec(scenario.execution_observation)
    return build_trace(scenario, original, replay, impact, exec_result, trace_id)


def test_built_trace_verifies(scenarios_by_id):
    trace = _build(scenarios_by_id["A_baseline"])
    verdict = verify_trace(trace)
    assert verdict["valid"] is True
    assert verdict["findings"] == []


def test_tampering_with_protected_field_is_detected(scenarios_by_id):
    trace = _build(scenarios_by_id["A_baseline"])
    tampered = copy.deepcopy(trace)
    tampered["scenario_id"] = "tampered"
    verdict = verify_trace(tampered)
    assert verdict["valid"] is False
    assert any("hash" in f.lower() for f in verdict["findings"])


def test_missing_required_field_fails(scenarios_by_id):
    trace = _build(scenarios_by_id["A_baseline"])
    broken = copy.deepcopy(trace)
    del broken["scenario_id"]
    verdict = verify_trace(broken)
    assert verdict["valid"] is False
    assert any("scenario_id" in f for f in verdict["findings"])


def test_missing_trace_integrity_fails(scenarios_by_id):
    trace = _build(scenarios_by_id["A_baseline"])
    broken = copy.deepcopy(trace)
    del broken["trace_integrity"]
    verdict = verify_trace(broken)
    assert verdict["valid"] is False


def test_key_order_does_not_change_hash(scenarios_by_id):
    trace = _build(scenarios_by_id["A_baseline"])
    reordered = {k: trace[k] for k in reversed(list(trace.keys()))}
    assert canonical_dumps({k: trace[k] for k in HASHED_TOP_LEVEL_FIELDS}) == canonical_dumps(
        {k: reordered[k] for k in HASHED_TOP_LEVEL_FIELDS}
    )
    assert compute_trace_hash(trace) == compute_trace_hash(reordered)


def test_repeated_builds_are_deterministic(scenarios_by_id):
    t1 = _build(scenarios_by_id["A_baseline"], trace_id="fixed")
    t2 = _build(scenarios_by_id["A_baseline"], trace_id="fixed")
    assert canonical_dumps(t1) == canonical_dumps(t2)