"""Replay engine.

The replay engine applies an explicitly supplied `EvaluationInputs` set to the
same action and returns a fresh `EvaluationResult`. It does NOT rewrite the
original decision. It does NOT claim that the original action executed,
executes, or was blocked.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    Action,
    EvaluationResult,
    Scenario,
)
from .policy_engine import evaluate


def run_original(scenario: Scenario) -> EvaluationResult:
    """Evaluate the action under the original inputs."""
    return evaluate(scenario.action, scenario.original_inputs)


def run_replay(scenario: Scenario) -> Optional[EvaluationResult]:
    """Evaluate the action under the replayed inputs.

    Returns None if no state change / replayed inputs were supplied.
    """
    if scenario.replayed_inputs is None:
        return None
    return evaluate(scenario.action, scenario.replayed_inputs)