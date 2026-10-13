"""Trace integrity helpers.

Defines canonical serialization and a verifier that:

- Validates required top-level fields exist.
- Recomputes the SHA-256 over the documented hash scope.
- Reports explicit invalid findings for malformed input rather than silently
  succeeding.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# Fields included in the hash scope. `trace_integrity` is intentionally excluded
# so the hash covers the payload, not the envelope that carries it.
HASHED_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "schema_version",
    "trace_id",
    "scenario_id",
    "action",
    "state_change",
    "original",
    "replay",
    "impact",
    "execution_authority",
    "verification",
)

REQUIRED_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "schema_version",
    "trace_id",
    "scenario_id",
    "action",
    "original",
    "impact",
    "execution_authority",
    "verification",
    "trace_integrity",
)


def canonical_dumps(value: Any) -> str:
    """Canonical JSON string used for hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def compute_trace_hash(trace: dict[str, Any]) -> str:
    hashed = {k: trace[k] for k in HASHED_TOP_LEVEL_FIELDS if k in trace}
    return hashlib.sha256(canonical_dumps(hashed).encode("utf-8")).hexdigest()


def verify_trace(trace: Any) -> dict[str, Any]:
    """Verify a trace's structure and hash.

    Returns a dict with:
        valid: bool
        findings: list[str]
        recomputed_hash: str | None
        recorded_hash: str | None
    """
    findings: list[str] = []

    if not isinstance(trace, dict):
        return {
            "valid": False,
            "findings": ["Trace is not a JSON object."],
            "recomputed_hash": None,
            "recorded_hash": None,
        }

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in trace:
            findings.append(f"Missing required top-level field: {field}")

    envelope = trace.get("trace_integrity")
    if not isinstance(envelope, dict):
        findings.append("trace_integrity must be an object.")
        return {
            "valid": False,
            "findings": findings,
            "recomputed_hash": None,
            "recorded_hash": None,
        }

    recorded = envelope.get("trace_hash")
    scope = envelope.get("hash_scope")
    if not isinstance(recorded, str):
        findings.append("trace_integrity.trace_hash must be a string.")
    if scope != list(HASHED_TOP_LEVEL_FIELDS):
        findings.append(
            "trace_integrity.hash_scope does not match the documented scope."
        )

    # Recompute using the documented scope regardless of the envelope's claim.
    recomputed = compute_trace_hash(trace)

    if isinstance(recorded, str) and recorded != recomputed:
        findings.append(
            "Recorded trace_hash does not match recomputed hash over the "
            "documented scope. Trace content may have been modified."
        )

    return {
        "valid": len(findings) == 0,
        "findings": findings,
        "recomputed_hash": recomputed,
        "recorded_hash": recorded if isinstance(recorded, str) else None,
    }