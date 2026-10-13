"""Replay engine tests.

Prove:
  - Replay uses the replayed inputs, not the original inputs.
  - Replay does not mutate the original decision.
  - A historical decision is not silently rewritten.
"""

from __future__ import annotations

from src.models import Decision
from src.replay_engine import run_original, run_replay


def test_replay_uses_replayed_inputs(scenarios_by_id):
    scenario = scenarios_by_id["B_authority_revoked"]
    original = run_original(scenario)
    replayed = run_replay(scenario)
    assert original.decision is Decision.ALLOW
    assert replayed is not None
    assert replayed.decision is Decision.DENY


def test_original_is_not_mutated(scenarios_by_id):
    scenario = scenarios_by_id["B_authority_revoked"]
    before = run_original(scenario)
    _ = run_replay(scenario)
    after = run_original(scenario)
    assert before.decision == after.decision
    assert before.reason_codes == after.reason_codes


def test_no_replay_when_absent(scenarios_by_id):
    scenario = scenarios_by_id["A_baseline"]
    assert run_replay(scenario) is None