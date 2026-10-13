"""Typed domain models for the DecisionAssure Boundary Replay Lab.

All models are pure dataclasses. They are deliberately small and explicit.
No global state is used anywhere in this project.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class Decision(str, Enum):
    """Admissibility / authorization decision values."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    NOT_CHECKED = "NOT_CHECKED"


class Impact(str, Enum):
    """Governance impact classification between original and replay."""

    UNCHANGED = "UNCHANGED"
    MATERIAL_CHANGE = "MATERIAL_CHANGE"
    NO_BASELINE = "NO_BASELINE"
    INVALID = "INVALID"


class ExecutionAuthorityStatus(str, Enum):
    """Execution-time authority observation status.

    NOT_CHECKED means no observation was supplied. It is NOT a denial and NOT
    an approval. It is an explicit statement that execution-time authority was
    not observed in this run.
    """

    NOT_CHECKED = "NOT_CHECKED"
    OBSERVED_ALLOW = "OBSERVED_ALLOW"
    OBSERVED_DENY = "OBSERVED_DENY"
    OBSERVED_INVALID = "OBSERVED_INVALID"


class ReasonCode(str, Enum):
    # Policy
    POLICY_RULE_MATCH_ALLOW = "POLICY_RULE_MATCH_ALLOW"
    POLICY_RULE_MATCH_DENY = "POLICY_RULE_MATCH_DENY"
    POLICY_RULE_MATCH_HOLD = "POLICY_RULE_MATCH_HOLD"
    POLICY_NO_MATCH = "POLICY_NO_MATCH"
    POLICY_VERSION_CHANGED = "POLICY_VERSION_CHANGED"

    # Authority (policy-relevant authority state)
    AUTHORITY_VALID = "AUTHORITY_VALID"
    AUTHORITY_REVOKED = "AUTHORITY_REVOKED"
    AUTHORITY_MISSING = "AUTHORITY_MISSING"
    AUTHORITY_INVALID_STATE = "AUTHORITY_INVALID_STATE"

    # Evidence
    EVIDENCE_FRESH = "EVIDENCE_FRESH"
    EVIDENCE_STALE = "EVIDENCE_STALE"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"

    # Impact
    IMPACT_UNCHANGED = "IMPACT_UNCHANGED"
    IMPACT_MATERIAL_CHANGE = "IMPACT_MATERIAL_CHANGE"
    IMPACT_NO_BASELINE = "IMPACT_NO_BASELINE"
    IMPACT_INVALID = "IMPACT_INVALID"

    # Execution authority
    EXEC_AUTH_NOT_CHECKED = "EXEC_AUTH_NOT_CHECKED"
    EXEC_AUTH_OBSERVED_ALLOW = "EXEC_AUTH_OBSERVED_ALLOW"
    EXEC_AUTH_OBSERVED_DENY = "EXEC_AUTH_OBSERVED_DENY"
    EXEC_AUTH_OBSERVED_INVALID = "EXEC_AUTH_OBSERVED_INVALID"


@dataclass(frozen=True)
class PolicyRule:
    """A single deterministic rule.

    match_actions: exact action_id strings this rule applies to ("*" = any).
    require_authority: if True, authority_state must be VALID to allow.
    require_fresh_evidence: if True, evidence freshness must be True.
    on_match: Decision to return if all requirements are satisfied.
    on_violation: Decision to return if a requirement fails.
    """

    rule_id: str
    match_actions: tuple[str, ...]
    require_authority: bool
    require_fresh_evidence: bool
    on_match: Decision
    on_violation: Decision


@dataclass(frozen=True)
class Policy:
    policy_id: str
    version: str
    rules: tuple[PolicyRule, ...]


@dataclass(frozen=True)
class AuthorityState:
    """Policy-relevant authority state at decision time."""

    subject_id: str
    state: str  # "VALID" | "REVOKED" | "UNKNOWN"
    source: str = "synthetic"


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    captured_at_seq: int
    max_age_seq: int
    source: str = "synthetic"

    def is_fresh(self, evaluation_seq: int) -> bool:
        if self.max_age_seq < 0:
            return False
        return (evaluation_seq - self.captured_at_seq) <= self.max_age_seq


@dataclass(frozen=True)
class Action:
    action_id: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationInputs:
    """Inputs used for a single admissibility evaluation."""

    policy: Policy
    authority: AuthorityState
    evidence: tuple[EvidenceRef, ...]
    evaluation_seq: int


@dataclass(frozen=True)
class EvaluationResult:
    decision: Decision
    reason_codes: tuple[ReasonCode, ...]
    matched_rule_id: Optional[str]
    explanation: str
    inputs: EvaluationInputs


@dataclass(frozen=True)
class ExecutionAuthorityObservation:
    """An explicitly supplied synthetic observation.

    `is_synthetic` must remain True in this demo. It documents that this
    observation is a fixture, not independently authenticated or
    hardware-rooted proof.
    """

    subject_id: str
    action_id: str
    observed_at_seq: int
    status: str  # "ALLOW" | "DENY" | "INVALID"
    observer: str
    is_synthetic: bool = True


@dataclass(frozen=True)
class ExecutionAuthorityResult:
    status: ExecutionAuthorityStatus
    reason_codes: tuple[ReasonCode, ...]
    explanation: str
    observation: Optional[ExecutionAuthorityObservation]


@dataclass(frozen=True)
class StateChange:
    """A single explicitly recorded governance-relevant change."""

    change_id: str
    kind: str  # "POLICY_VERSION" | "AUTHORITY_STATE" | "EVIDENCE_FRESHNESS"
    description: str
    applied_at_seq: int


@dataclass(frozen=True)
class ImpactFinding:
    field_path: str
    original_value: Any
    replayed_value: Any
    changed: bool
    note: str


@dataclass(frozen=True)
class ImpactAnalysis:
    classification: Impact
    findings: tuple[ImpactFinding, ...]
    reason_codes: tuple[ReasonCode, ...]
    explanation: str


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    title: str
    description: str
    action: Action
    original_inputs: EvaluationInputs
    state_change: Optional[StateChange]
    replayed_inputs: Optional[EvaluationInputs]
    execution_observation: Optional[ExecutionAuthorityObservation]


def to_jsonable(value: Any) -> Any:
    """Recursively convert dataclasses/enums/tuples into JSON-friendly data."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(value).items()}
    return value