"""Policy engine tests.

Prove:
  - Deterministic evaluation under fixed inputs.
  - Authority revocation yields DENY when the rule requires authority.
  - Missing evidence yields the rule's on_violation.
  - Invalid authority state yields HOLD.
  - Identical inputs -> identical decisions.
"""

from __future__ import annotations

from src.models import Action, Decision, EvaluationInputs
from src.policy_engine import evaluate


def test_baseline_allows(baseline_inputs, action):
    result = evaluate(action, baseline_inputs)
    assert result.decision is Decision.ALLOW


def test_revoked_authority_denies(revoked_inputs, action):
    result = evaluate(action, revoked_inputs)
    assert result.decision is Decision.DENY


def test_missing_evidence_violates_rule(action, baseline_inputs):
    from dataclasses import replace
    inputs = replace(baseline_inputs, evidence=())
    result = evaluate(action, inputs)
    assert result.decision is Decision.DENY


def test_invalid_authority_state_holds(action, baseline_inputs):
    from dataclasses import replace
    from src.models import AuthorityState
    inputs = replace(
        baseline_inputs,
        authority=AuthorityState(subject_id="agent-treasury-01", state="UNKNOWN"),
    )
    result = evaluate(action, inputs)
    assert result.decision is Decision.HOLD


def test_determinism(baseline_inputs, action):
    r1 = evaluate(action, baseline_inputs)
    r2 = evaluate(action, baseline_inputs)
    assert r1.decision == r2.decision
    assert r1.reason_codes == r2.reason_codes
    assert r1.matched_rule_id == r2.matched_rule_id