"""Impact analysis tests.

Prove:
  - Material change is detected (authority revoked, policy tightened, stale evidence).
  - No material change yields UNCHANGED.
  - Impact is not invented when no replay is supplied.
"""

from __future__ import annotations

from src.impact_analysis import analyze
from src.models import Impact
from src.replay_engine import run_original, run_replay


def test_authority_revoked_is_material(scenarios_by_id):
    s = scenarios_by_id["B_authority_revoked"]
    impact = analyze(run_original(s), run_replay(s))
    assert impact.classification is Impact.MATERIAL_CHANGE


def test_policy_tightened_is_material(scenarios_by_id):
    s = scenarios_by_id["C_policy_tightened"]
    impact = analyze(run_original(s), run_replay(s))
    assert impact.classification is Impact.MATERIAL_CHANGE
    paths = {f.field_path for f in impact.findings if f.changed}
    assert "policy.version" in paths


def test_stale_evidence_is_material(scenarios_by_id):
    s = scenarios_by_id["D_evidence_stale"]
    impact = analyze(run_original(s), run_replay(s))
    assert impact.classification is Impact.MATERIAL_CHANGE
    paths = {f.field_path for f in impact.findings if f.changed}
    assert "evidence.fresh_at_evaluation" in paths


def test_no_change_is_unchanged(scenarios_by_id):
    s = scenarios_by_id["E_no_change"]
    impact = analyze(run_original(s), run_replay(s))
    assert impact.classification is Impact.UNCHANGED


def test_no_baseline_when_no_replay(scenarios_by_id):
    s = scenarios_by_id["A_baseline"]
    impact = analyze(run_original(s), None)
    assert impact.classification is Impact.NO_BASELINE