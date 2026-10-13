"""Runtime fixture loader.

Loads synthetic scenarios from fixtures/scenarios.json into typed models.

This module is the single source of truth for turning the JSON fixture file
into typed Scenario objects. It is imported by:

  - app.py (runtime)
  - tests/conftest.py (test fixtures)

It deliberately does NOT import pytest, and it does NOT live under tests/.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    Action,
    AuthorityState,
    Decision,
    EvaluationInputs,
    EvidenceRef,
    ExecutionAuthorityObservation,
    Policy,
    PolicyRule,
    Scenario,
    StateChange,
)

FIXTURES_PATH = (
    Path(__file__).resolve().parent.parent / "fixtures" / "scenarios.json"
)


def _eval_inputs_from_dict(d: dict) -> EvaluationInputs:
    rules = tuple(
        PolicyRule(
            rule_id=r["rule_id"],
            match_actions=tuple(r["match_actions"]),
            require_authority=r["require_authority"],
            require_fresh_evidence=r["require_fresh_evidence"],
            on_match=Decision(r["on_match"]),
            on_violation=Decision(r["on_violation"]),
        )
        for r in d["policy"]["rules"]
    )
    policy = Policy(
        policy_id=d["policy"]["policy_id"],
        version=d["policy"]["version"],
        rules=rules,
    )
    authority = AuthorityState(
        subject_id=d["authority"]["subject_id"],
        state=d["authority"]["state"],
        source=d["authority"].get("source", "synthetic"),
    )
    evidence = tuple(
        EvidenceRef(
            evidence_id=e["evidence_id"],
            captured_at_seq=e["captured_at_seq"],
            max_age_seq=e["max_age_seq"],
            source=e.get("source", "synthetic"),
        )
        for e in d["evidence"]
    )
    return EvaluationInputs(
        policy=policy,
        authority=authority,
        evidence=evidence,
        evaluation_seq=d["evaluation_seq"],
    )


def load_scenarios(path: Path | None = None) -> list[Scenario]:
    """Load all scenarios from the fixtures file.

    Raises a clear error if the file is missing or malformed.
    """
    p = path or FIXTURES_PATH
    if not p.exists():
        raise FileNotFoundError(f"Fixtures file not found: {p}")

    try:
        raw = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Fixtures file is not valid JSON: {p} — {exc}") from exc

    if "scenarios" not in raw or not isinstance(raw["scenarios"], list):
        raise ValueError(
            f"Fixtures file must contain a top-level 'scenarios' list: {p}"
        )

    scenarios: list[Scenario] = []
    for s in raw["scenarios"]:
        sc = Scenario(
            scenario_id=s["scenario_id"],
            title=s["title"],
            description=s["description"],
            action=Action(
                action_id=s["action"]["action_id"],
                parameters=dict(s["action"].get("parameters", {})),
            ),
            original_inputs=_eval_inputs_from_dict(s["original"]),
            state_change=None
            if s.get("state_change") is None
            else StateChange(
                change_id=s["state_change"]["change_id"],
                kind=s["state_change"]["kind"],
                description=s["state_change"]["description"],
                applied_at_seq=s["state_change"]["applied_at_seq"],
            ),
            replayed_inputs=None
            if s.get("replay") is None
            else _eval_inputs_from_dict(s["replay"]),
            execution_observation=None
            if s.get("execution_observation") is None
            else ExecutionAuthorityObservation(
                subject_id=s["execution_observation"]["subject_id"],
                action_id=s["execution_observation"]["action_id"],
                observed_at_seq=s["execution_observation"]["observed_at_seq"],
                status=s["execution_observation"]["status"],
                observer=s["execution_observation"]["observer"],
                is_synthetic=s["execution_observation"].get("is_synthetic", True),
            ),
        )
        scenarios.append(sc)
    return scenarios