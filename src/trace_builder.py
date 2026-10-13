"""Builds the machine-readable JSON trace.

Canonicalization rules (must remain stable across runs):

1. JSON is serialized with `sort_keys=True`.
2. Separators are `(",", ":")` — no extra whitespace.
3. Only the following top-level fields participate in the trace hash:
       schema_version, trace_id, scenario_id, action, original, replay,
       impact, execution_authority, state_change, verification
   `trace_integrity` itself is excluded, so the hash covers the payload
   and not the envelope that carries the hash.
4. Nested dicts are canonicalized recursively by the same rules.

`trace_integrity.hash_scope` documents exactly which field paths were hashed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .models import (
    EvaluationResult,
    ExecutionAuthorityResult,
    ImpactAnalysis,
    Scenario,
    to_jsonable,
)
from .trace_integrity import HASHED_TOP_LEVEL_FIELDS, canonical_dumps

SCHEMA_VERSION = "decisionassure.boundary-replay-lab/1.0"


def _evaluation_payload(result: EvaluationResult) -> dict[str, Any]:
    return {
        "decision": result.decision.value,
        "reason_codes": [r.value for r in result.reason_codes],
        "matched_rule_id": result.matched_rule_id,
        "explanation": result.explanation,
        "inputs": {
            "policy": {
                "policy_id": result.inputs.policy.policy_id,
                "version": result.inputs.policy.version,
            },
            "authority": {
                "subject_id": result.inputs.authority.subject_id,
                "state": result.inputs.authority.state,
                "source": result.inputs.authority.source,
            },
            "evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "captured_at_seq": e.captured_at_seq,
                    "max_age_seq": e.max_age_seq,
                    "source": e.source,
                    "is_fresh_at_evaluation": e.is_fresh(
                        result.inputs.evaluation_seq
                    ),
                }
                for e in result.inputs.evidence
            ],
            "evaluation_seq": result.inputs.evaluation_seq,
        },
    }


def _execution_payload(result: ExecutionAuthorityResult) -> dict[str, Any]:
    obs = result.observation
    return {
        "status": result.status.value,
        "reason_codes": [r.value for r in result.reason_codes],
        "explanation": result.explanation,
        "observation": None
        if obs is None
        else {
            "subject_id": obs.subject_id,
            "action_id": obs.action_id,
            "observed_at_seq": obs.observed_at_seq,
            "status": obs.status,
            "observer": obs.observer,
            "is_synthetic": obs.is_synthetic,
        },
    }


def _impact_payload(impact: ImpactAnalysis) -> dict[str, Any]:
    return {
        "classification": impact.classification.value,
        "reason_codes": [r.value for r in impact.reason_codes],
        "explanation": impact.explanation,
        "findings": [
            {
                "field_path": f.field_path,
                "original_value": f.original_value,
                "replayed_value": f.replayed_value,
                "changed": f.changed,
                "note": f.note,
            }
            for f in impact.findings
        ],
    }


def build_trace(
    scenario: Scenario,
    original: EvaluationResult,
    replay: EvaluationResult | None,
    impact: ImpactAnalysis,
    execution: ExecutionAuthorityResult,
    trace_id: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "trace_id": trace_id,
        "scenario_id": scenario.scenario_id,
        "action": {
            "action_id": scenario.action.action_id,
            "parameters": to_jsonable(scenario.action.parameters),
        },
        "state_change": None
        if scenario.state_change is None
        else {
            "change_id": scenario.state_change.change_id,
            "kind": scenario.state_change.kind,
            "description": scenario.state_change.description,
            "applied_at_seq": scenario.state_change.applied_at_seq,
        },
        "original": _evaluation_payload(original),
        "replay": None if replay is None else _evaluation_payload(replay),
        "impact": _impact_payload(impact),
        "execution_authority": _execution_payload(execution),
        "verification": {
            "notes": [
                "Synthetic data only. No real action was executed, authorized, blocked, or rolled back.",
                "Replay is a deterministic comparison under declared inputs.",
                "Replay does not prove the original action actually executed.",
                "SHA-256 establishes content integrity, not truth or independent authenticity.",
                "Execution authority is NOT_CHECKED unless a relevant observation is explicitly supplied.",
                "A synthetic execution-authority observation is not hardware-rooted proof.",
                "No claim of production readiness, certification, or security assurance is made.",
            ],
            "disclaimer": (
                "Illustrative local reference demo. Not a security product. "
                "Not an integration with Certor. No Certor private implementation "
                "or proprietary information is assumed."
            ),
        },
    }

    hashed = {k: payload[k] for k in HASHED_TOP_LEVEL_FIELDS if k in payload}
    digest = hashlib.sha256(canonical_dumps(hashed).encode("utf-8")).hexdigest()

    payload["trace_integrity"] = {
        "algorithm": "sha256",
        "canonicalization": (
            "json.dumps(sort_keys=True, separators=(',',':')) over the "
            "selected top-level fields listed in hash_scope."
        ),
        "hash_scope": list(HASHED_TOP_LEVEL_FIELDS),
        "trace_hash": digest,
        "notes": [
            "The trace_integrity envelope is excluded from its own hash.",
            "Recomputing the hash over the same scope must reproduce trace_hash.",
            "Modifying any protected field invalidates the recorded hash.",
            "A hash does not establish truth, signer identity, or external timestamp authenticity.",
        ],
    }
    return payload