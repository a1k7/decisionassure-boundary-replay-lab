"""Shared test fixtures. All fixtures are deterministic and synthetic."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.models import (
    Action,
    AuthorityState,
    EvaluationInputs,
    EvidenceRef,
    ExecutionAuthorityObservation,
    Policy,
    PolicyRule,
    Scenario,
    StateChange,
)

FIXTURES_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "scenarios.json"


def _rule(
    rule_id: str = "r1",
    actions=("release_funds",),
    require_authority: bool = True,
    require_fresh: bool = True,
    on_match: str = "ALLOW",
    on_violation: str = "DENY",
) -> dict:
    return {
        "rule_id": rule_id,
        "match_actions": list(actions),
        "require_authority": require_authority,
        "require_fresh_evidence": require_fresh,
        "on_match": on_match,
        "on_violation": on_violation,
    }


def _policy(version: str = "1.0", rules=None) -> dict:
    if rules is None:
        rules = [_rule()]
    return {"policy_id": "treasury.release", "version": version, "rules": rules}


def _inputs(
    *,
    policy: dict | None = None,
    authority_state: str = "VALID",
    evidence=(("ev-1", 100, 10),),
    evaluation_seq: int = 105,
) -> dict:
    return {
        "policy": policy or _policy(),
        "authority": {
            "subject_id": "agent-treasury-01",
            "state": authority_state,
            "source": "synthetic",
        },
        "evidence": [
            {
                "evidence_id": eid,
                "captured_at_seq": cap,
                "max_age_seq": age,
                "source": "synthetic",
            }
            for (eid, cap, age) in evidence
        ],
        "evaluation_seq": evaluation_seq,
    }


@pytest.fixture
def action() -> Action:
    return Action(action_id="release_funds", parameters={"amount": 2500})


@pytest.fixture
def baseline_inputs() -> EvaluationInputs:
    return EvaluationInputs(
        policy=Policy(
            policy_id="treasury.release",
            version="1.0",
            rules=(
                PolicyRule(
                    rule_id="release-default",
                    match_actions=("release_funds",),
                    require_authority=True,
                    require_fresh_evidence=True,
                    on_match=__import__("src.models", fromlist=["Decision"]).Decision.ALLOW,
                    on_violation=__import__("src.models", fromlist=["Decision"]).Decision.DENY,
                ),
            ),
        ),
        authority=AuthorityState(subject_id="agent-treasury-01", state="VALID"),
        evidence=(EvidenceRef(evidence_id="ev-1", captured_at_seq=100, max_age_seq=10),),
        evaluation_seq=105,
    )


@pytest.fixture
def revoked_inputs() -> EvaluationInputs:
    return EvaluationInputs(
        policy=Policy(
            policy_id="treasury.release",
            version="1.0",
            rules=(
                PolicyRule(
                    rule_id="release-default",
                    match_actions=("release_funds",),
                    require_authority=True,
                    require_fresh_evidence=True,
                    on_match=__import__("src.models", fromlist=["Decision"]).Decision.ALLOW,
                    on_violation=__import__("src.models", fromlist=["Decision"]).Decision.DENY,
                ),
            ),
        ),
        authority=AuthorityState(subject_id="agent-treasury-01", state="REVOKED"),
        evidence=(EvidenceRef(evidence_id="ev-1", captured_at_seq=100, max_age_seq=10),),
        evaluation_seq=145,
    )


@pytest.fixture
def synthetic_exec_observation_allow() -> ExecutionAuthorityObservation:
    return ExecutionAuthorityObservation(
        subject_id="agent-treasury-01",
        action_id="release_funds",
        observed_at_seq=105,
        status="ALLOW",
        observer="synthetic-observer",
        is_synthetic=True,
    )


def _eval_inputs_from_dict(d: dict) -> EvaluationInputs:
    from src.models import Decision

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


def load_scenarios() -> list[Scenario]:
    raw = json.loads(FIXTURES_PATH.read_text())
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


@pytest.fixture
def scenarios() -> list[Scenario]:
    return load_scenarios()


@pytest.fixture
def scenarios_by_id(scenarios):
    return {s.scenario_id: s for s in scenarios}


@pytest.fixture
def raw_fixtures() -> dict:
    return json.loads(FIXTURES_PATH.read_text())