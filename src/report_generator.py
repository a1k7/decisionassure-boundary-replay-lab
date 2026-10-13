"""Human-readable report generation (Markdown)."""

from __future__ import annotations

from typing import Any


def _kv(label: str, value: Any) -> str:
    return f"- **{label}:** {value}"


def generate_report(trace: dict[str, Any]) -> str:
    original = trace.get("original") or {}
    replay = trace.get("replay")
    impact = trace.get("impact") or {}
    exec_auth = trace.get("execution_authority") or {}
    integrity = trace.get("trace_integrity") or {}
    verification = trace.get("verification") or {}

    lines: list[str] = []
    lines.append(f"# DecisionAssure Boundary Replay Lab — Report")
    lines.append("")
    lines.append(f"**Trace ID:** `{trace.get('trace_id')}`  ")
    lines.append(f"**Scenario:** `{trace.get('scenario_id')}`  ")
    lines.append(f"**Schema:** `{trace.get('schema_version')}`")
    lines.append("")

    lines.append("## Action")
    action = trace.get("action") or {}
    lines.append(_kv("Action ID", action.get("action_id")))
    lines.append(_kv("Parameters", action.get("parameters")))
    lines.append("")

    lines.append("## ORIGINAL ADMISSIBILITY")
    lines.append(_kv("Decision", original.get("decision")))
    lines.append(_kv("Matched rule", original.get("matched_rule_id")))
    lines.append(_kv("Reason codes", ", ".join(original.get("reason_codes", []))))
    lines.append(_kv("Explanation", original.get("explanation")))
    o_inputs = original.get("inputs", {})
    lines.append(_kv("Policy", o_inputs.get("policy")))
    lines.append(_kv("Authority", o_inputs.get("authority")))
    lines.append(_kv("Evaluation seq", o_inputs.get("evaluation_seq")))
    lines.append("")

    lines.append("## State change")
    sc = trace.get("state_change")
    if sc is None:
        lines.append("_No state change recorded for this scenario._")
    else:
        lines.append(_kv("Change ID", sc.get("change_id")))
        lines.append(_kv("Kind", sc.get("kind")))
        lines.append(_kv("Applied at seq", sc.get("applied_at_seq")))
        lines.append(_kv("Description", sc.get("description")))
    lines.append("")

    lines.append("## REPLAYED ADMISSIBILITY")
    if replay is None:
        lines.append("_No replay was performed for this scenario._")
    else:
        lines.append(_kv("Decision", replay.get("decision")))
        lines.append(_kv("Matched rule", replay.get("matched_rule_id")))
        lines.append(_kv("Reason codes", ", ".join(replay.get("reason_codes", []))))
        lines.append(_kv("Explanation", replay.get("explanation")))
        r_inputs = replay.get("inputs", {})
        lines.append(_kv("Policy", r_inputs.get("policy")))
        lines.append(_kv("Authority", r_inputs.get("authority")))
        lines.append(_kv("Evaluation seq", r_inputs.get("evaluation_seq")))
    lines.append("")

    lines.append("## GOVERNANCE IMPACT")
    lines.append(_kv("Classification", impact.get("classification")))
    lines.append(_kv("Reason codes", ", ".join(impact.get("reason_codes", []))))
    lines.append(_kv("Explanation", impact.get("explanation")))
    lines.append("")
    lines.append("| Field | Original | Replayed | Changed | Note |")
    lines.append("|---|---|---|---|---|")
    for f in impact.get("findings", []):
        lines.append(
            f"| `{f.get('field_path')}` | `{f.get('original_value')}` | "
            f"`{f.get('replayed_value')}` | {f.get('changed')} | {f.get('note')} |"
        )
    lines.append("")

    lines.append("## EXECUTION AUTHORITY")
    lines.append(_kv("Status", exec_auth.get("status")))
    lines.append(_kv("Reason codes", ", ".join(exec_auth.get("reason_codes", []))))
    lines.append(_kv("Explanation", exec_auth.get("explanation")))
    obs = exec_auth.get("observation")
    if obs is None:
        lines.append("_No execution-authority observation was supplied._")
    else:
        lines.append(_kv("Observation", obs))
        lines.append(
            "_This observation is synthetic and is not independently "
            "authenticated or hardware-rooted proof._"
        )
    lines.append("")

    lines.append("## TRACE INTEGRITY")
    lines.append(_kv("Algorithm", integrity.get("algorithm")))
    lines.append(_kv("Hash scope", ", ".join(integrity.get("hash_scope", []))))
    lines.append(_kv("Recorded hash", integrity.get("trace_hash")))
    for note in integrity.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")

    lines.append("## LIMITATIONS")
    for note in verification.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    lines.append(f"> {verification.get('disclaimer', '')}")
    lines.append("")

    return "\n".join(lines)