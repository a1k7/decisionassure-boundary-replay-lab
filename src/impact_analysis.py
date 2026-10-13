"""Structured comparison between an original and a replayed decision."""

from __future__ import annotations

from typing import Any, Optional

from .models import (
    EvaluationResult,
    Impact,
    ImpactAnalysis,
    ImpactFinding,
    ReasonCode,
)


def _finding(
    field_path: str,
    original: Any,
    replayed: Any,
    note: str,
) -> ImpactFinding:
    return ImpactFinding(
        field_path=field_path,
        original_value=original,
        replayed_value=replayed,
        changed=(original != replayed),
        note=note,
    )


def analyze(
    original: EvaluationResult,
    replayed: Optional[EvaluationResult],
) -> ImpactAnalysis:
    if replayed is None:
        return ImpactAnalysis(
            classification=Impact.NO_BASELINE,
            findings=(),
            reason_codes=(ReasonCode.IMPACT_NO_BASELINE,),
            explanation="No replayed evaluation was supplied; impact cannot be computed.",
        )

    findings: list[ImpactFinding] = []

    # Policy
    o_pol = original.inputs.policy
    r_pol = replayed.inputs.policy
    findings.append(
        _finding(
            "policy.version",
            f"{o_pol.policy_id}@{o_pol.version}",
            f"{r_pol.policy_id}@{r_pol.version}",
            "Policy identifier and version used for each evaluation.",
        )
    )

    # Authority state
    findings.append(
        _finding(
            "authority.state",
            original.inputs.authority.state,
            replayed.inputs.authority.state,
            "Policy-relevant authority state at evaluation time.",
        )
    )

    # Evidence freshness (evaluated against each side's evaluation_seq)
    o_fresh = all(e.is_fresh(original.inputs.evaluation_seq) for e in original.inputs.evidence)
    r_fresh = all(e.is_fresh(replayed.inputs.evaluation_seq) for e in replayed.inputs.evidence)
    findings.append(
        _finding(
            "evidence.fresh_at_evaluation",
            o_fresh,
            r_fresh,
            "Whether every evidence reference was fresh under its own evaluation_seq.",
        )
    )

    # Evaluation sequence
    findings.append(
        _finding(
            "evaluation_seq",
            original.inputs.evaluation_seq,
            replayed.inputs.evaluation_seq,
            "Logical sequence used for freshness and audit ordering.",
        )
    )

    # Decision
    findings.append(
        _finding(
            "decision",
            original.decision.value,
            replayed.decision.value,
            "Admissibility decision produced by the policy engine.",
        )
    )

    material = any(
        f.changed for f in findings if f.field_path != "evaluation_seq"
    )

    if not material:
        return ImpactAnalysis(
            classification=Impact.UNCHANGED,
            findings=tuple(findings),
            reason_codes=(ReasonCode.IMPACT_UNCHANGED,),
            explanation=(
                "No material governance input changed between original and replay; "
                "decision is stable."
            ),
        )

    return ImpactAnalysis(
        classification=Impact.MATERIAL_CHANGE,
        findings=tuple(findings),
        reason_codes=(ReasonCode.IMPACT_MATERIAL_CHANGE,),
        explanation=(
            "At least one material governance input changed between original and "
            "replay. See findings for the exact fields."
        ),
    )