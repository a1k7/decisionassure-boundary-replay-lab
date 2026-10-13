"""Execution-authority tests.

Prove:
  - Missing observation -> NOT_CHECKED (never ALLOW, never DENY).
  - Supplied observation is evaluated separately from replay.
  - Invalid status -> OBSERVED_INVALID.
"""

from __future__ import annotations

from src.execution_authority import evaluate
from src.models import (
    ExecutionAuthorityObservation,
    ExecutionAuthorityStatus,
)


def test_no_observation_is_not_checked():
    result = evaluate(None)
    assert result.status is ExecutionAuthorityStatus.NOT_CHECKED


def test_synthetic_allow_is_observed_allow(synthetic_exec_observation_allow):
    result = evaluate(synthetic_exec_observation_allow)
    assert result.status is ExecutionAuthorityStatus.OBSERVED_ALLOW
    assert result.observation is not None
    assert result.observation.is_synthetic is True


def test_synthetic_deny_is_observed_deny():
    obs = ExecutionAuthorityObservation(
        subject_id="agent-treasury-01",
        action_id="release_funds",
        observed_at_seq=105,
        status="DENY",
        observer="synthetic-observer",
        is_synthetic=True,
    )
    result = evaluate(obs)
    assert result.status is ExecutionAuthorityStatus.OBSERVED_DENY


def test_invalid_status_is_observed_invalid():
    obs = ExecutionAuthorityObservation(
        subject_id="agent-treasury-01",
        action_id="release_funds",
        observed_at_seq=105,
        status="MAYBE",
        observer="synthetic-observer",
        is_synthetic=True,
    )
    result = evaluate(obs)
    assert result.status is ExecutionAuthorityStatus.OBSERVED_INVALID