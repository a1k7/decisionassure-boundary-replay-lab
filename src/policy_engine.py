"""Deterministic policy evaluation.

Rules are evaluated in the order they are declared. The first rule whose
`match_actions` contains the action_id (or "*") determines the outcome.

No LLM, no randomness, no I/O. Identical inputs always produce identical
outputs.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    Action,
    Decision,
    EvaluationInputs,
    EvaluationResult,
    PolicyRule,
    ReasonCode,
)


def _match_rule(rule: PolicyRule, action: Action) -> bool:
    return "*" in rule.match_actions or action.action_id in rule.match_actions


def _evaluate_rule(
    rule: PolicyRule, inputs: EvaluationInputs
) -> tuple[Decision, list[ReasonCode]]:
    reasons: list[ReasonCode] = []

    # Authority check.
    if rule.require_authority:
        state = inputs.authority.state
        if state == "VALID":
            reasons.append(ReasonCode.AUTHORITY_VALID)
        elif state == "REVOKED":
            reasons.append(ReasonCode.AUTHORITY_REVOKED)
            return rule.on_violation, reasons
        else:
            reasons.append(ReasonCode.AUTHORITY_INVALID_STATE)
            return Decision.HOLD, reasons
    else:
        reasons.append(ReasonCode.AUTHORITY_VALID)

    # Evidence freshness check.
    if rule.require_fresh_evidence:
        if not inputs.evidence:
            reasons.append(ReasonCode.EVIDENCE_MISSING)
            return rule.on_violation, reasons
        all_fresh = all(e.is_fresh(inputs.evaluation_seq) for e in inputs.evidence)
        if all_fresh:
            reasons.append(ReasonCode.EVIDENCE_FRESH)
        else:
            reasons.append(ReasonCode.EVIDENCE_STALE)
            return rule.on_violation, reasons
    else:
        reasons.append(ReasonCode.EVIDENCE_FRESH)

    reasons.append(
        {
            Decision.ALLOW: ReasonCode.POLICY_RULE_MATCH_ALLOW,
            Decision.DENY: ReasonCode.POLICY_RULE_MATCH_DENY,
            Decision.HOLD: ReasonCode.POLICY_RULE_MATCH_HOLD,
        }[rule.on_match]
    )
    return rule.on_match, reasons


def evaluate(
    action: Action,
    inputs: EvaluationInputs,
) -> EvaluationResult:
    """Evaluate a single action under a single set of inputs."""
    for rule in inputs.policy.rules:
        if _match_rule(rule, action):
            decision, reasons = _evaluate_rule(rule, inputs)
            return EvaluationResult(
                decision=decision,
                reason_codes=tuple(reasons),
                matched_rule_id=rule.rule_id,
                explanation=(
                    f"Rule '{rule.rule_id}' matched action '{action.action_id}' "
                    f"under policy {inputs.policy.policy_id}@{inputs.policy.version}."
                ),
                inputs=inputs,
            )

    return EvaluationResult(
        decision=Decision.HOLD,
        reason_codes=(ReasonCode.POLICY_NO_MATCH,),
        matched_rule_id=None,
        explanation=(
            f"No rule matched action '{action.action_id}'. Fail-safe: HOLD."
        ),
        inputs=inputs,
    )