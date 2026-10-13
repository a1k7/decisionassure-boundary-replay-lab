"""Execution-time authority evaluation.

This module is deliberately separate from replay. It answers a different
question:

    "Was execution-time authority independently observed for this action?"

If no observation is supplied, the result is NOT_CHECKED. That is NOT a
denial and NOT an approval. A synthetic observation is labeled as synthetic
and is NOT proof of hardware-rooted or independently authenticated
enforcement.
"""

from __future__ import annotations

from typing import Optional

from .models import (
    ExecutionAuthorityObservation,
    ExecutionAuthorityResult,
    ExecutionAuthorityStatus,
    ReasonCode,
)


def evaluate(
    observation: Optional[ExecutionAuthorityObservation],
) -> ExecutionAuthorityResult:
    if observation is None:
        return ExecutionAuthorityResult(
            status=ExecutionAuthorityStatus.NOT_CHECKED,
            reason_codes=(ReasonCode.EXEC_AUTH_NOT_CHECKED,),
            explanation=(
                "No execution-time authority observation was supplied. "
                "Execution authority is NOT_CHECKED. This is not a denial and "
                "not an approval."
            ),
            observation=None,
        )

    status_raw = observation.status
    if status_raw == "ALLOW":
        return ExecutionAuthorityResult(
            status=ExecutionAuthorityStatus.OBSERVED_ALLOW,
            reason_codes=(ReasonCode.EXEC_AUTH_OBSERVED_ALLOW,),
            explanation=(
                "A synthetic execution-authority observation reports ALLOW. "
                "This is a supplied observation, not independently "
                "authenticated or hardware-rooted proof."
            ),
            observation=observation,
        )
    if status_raw == "DENY":
        return ExecutionAuthorityResult(
            status=ExecutionAuthorityStatus.OBSERVED_DENY,
            reason_codes=(ReasonCode.EXEC_AUTH_OBSERVED_DENY,),
            explanation=(
                "A synthetic execution-authority observation reports DENY. "
                "This is a supplied observation, not independently "
                "authenticated or hardware-rooted proof."
            ),
            observation=observation,
        )

    return ExecutionAuthorityResult(
        status=ExecutionAuthorityStatus.OBSERVED_INVALID,
        reason_codes=(ReasonCode.EXEC_AUTH_OBSERVED_INVALID,),
        explanation=(
            f"Execution-authority observation had unrecognized status "
            f"{status_raw!r}. Reported as OBSERVED_INVALID."
        ),
        observation=observation,
    )