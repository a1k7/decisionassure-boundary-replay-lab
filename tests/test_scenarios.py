"""Integration tests over the packaged scenarios.

Prove:
  - Each scenario produces the expected original/replay decisions.
  - Execution-authority is NOT_CHECKED unless an observation is supplied.
  - No scenario silently rewrites the original decision.
  - ALLOW does not imply execution authorization.
"""

from __future__ import annotations

from src.execution_authority import evaluate as eval_exec
from src.impact_analysis import analyze
from src.models import (
    Decision,
    ExecutionAuthorityStatus,
    Impact,
)
from src.replay_engine import run_original, run_replay


def test_A_baseline(scenarios_by_id):
    s = scenarios_by_id["A_baseline"]
    original = run_original(s)
    assert original.decision is Decision.ALLOW
    assert run_replay(s) is None


def test_B_authority_revoked(scenarios_by_id):
    s = scenarios_by_id["B_authority_revoked"]
    assert run_original(s).decision is Decision.ALLOW
    assert run_replay(s).decision is Decision.DENY
    impact = analyze(run_original(s), run_replay(s))
    assert impact.classification is Impact.MATERIAL_CHANGE


def test_C_policy_tightened(scenarios_by_id):
    s = scenarios_by_id["C_policy_tightened"]
    assert run_original(s).decision is Decision.ALLOW
    assert run_replay(s).decision is Decision.DENY
    impact = analyze(run_original(s), run_replay(s))
    assert impact.classification is Impact.MATERIAL_CHANGE


def test_D_evidence_stale(scenarios_by_id):
    s = scenarios_by_id["D_evidence_stale"]
    assert run_original(s).decision is Decision.ALLOW
    assert run_replay(s).decision is Decision.DENY


def test_E_no_change(scenarios_by_id):
    s = scenarios_by_id["E_no_change"]
    assert run_original(s).decision is Decision.ALLOW
    assert run_replay(s).decision is Decision.ALLOW
    impact = analyze(run_original(s), run_replay(s))
    assert impact.classification is Impact.UNCHANGED


def test_F_execution_not_observed(scenarios_by_id):
    s = scenarios_by_id["F_exec_not_observed"]
    original = run_original(s)
    assert original.decision is Decision.ALLOW
    exec_result = eval_exec(s.execution_observation)
    assert exec_result.status is ExecutionAuthorityStatus.NOT_CHECKED


def test_allow_does_not_imply_execution_authorization(scenarios_by_id):
    """An ALLOW decision is not evidence that execution was authorized."""
    s = scenarios_by_id["F_exec_not_observed"]
    assert run_original(s).decision is Decision.ALLOW
    assert eval_exec(s.execution_observation).status is ExecutionAuthorityStatus.NOT_CHECKED