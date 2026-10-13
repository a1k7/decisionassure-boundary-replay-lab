
# DecisionAssure Boundary Replay Lab

A deterministic, local, synthetic demonstration that makes a single architectural
distinction concrete:

> **Admissibility after change ≠ Current authority at execution.**

This project is an engineering reference. It is **not** a security product,
**not** a Certor integration, and **not** production-ready.

## What it demonstrates

1. A simulated AI agent proposes a consequential action.
2. DecisionAssure-style evaluation runs against a declared policy, authority
   state, and evidence state.
3. The original decision and its inputs are recorded.
4. A governance-relevant state change occurs (policy version, authority state,
   or evidence freshness).
5. The same action and the historical evidence references are replayed under
   the changed conditions.
6. A structured impact analysis shows which conditions changed and whether
   admissibility changed.
7. A **separate** execution-authority evaluation reports whether execution-time
   authority was observed. If no observation is supplied, the result is
   `NOT_CHECKED` — never `ALLOW`.
8. A machine-readable JSON trace and a Markdown report are exported.

## Decision semantics

- `ALLOW` — the policy engine matched a rule whose requirements were satisfied.
- `DENY` — the policy engine matched a rule whose requirements were violated.
- `HOLD` — the policy engine could not safely decide (e.g., invalid state).
- `NOT_CHECKED` — execution-time authority was not observed. This is **not** a
  denial and **not** an approval.

## Replay vs execution authority

These are different questions:

- **Replay** asks: given a declared change to governance state, would the same
  action still be admissible?
- **Execution authority** asks: at the moment of execution, did current
  authority exist?

Replay uses the **declared replayed inputs**, not whatever the system's
"current" state happens to be. This demo never reads live state. That
separation is deliberate: it lets the operator reason about *which specific
input* changed.

This demo never conflates replay and execution authority. An `ALLOW` in the
admissibility panel does **not** imply execution-time authorization.
Conversely, `NOT_CHECKED` in the execution-authority panel does **not** mean
the action was denied. It means the question was not answered.

## Scenarios

| ID | Name | Expected |
|---|---|---|
| A | Baseline | original `ALLOW`, no replay |
| B | Authority revoked | original `ALLOW`, replay `DENY`, impact `MATERIAL_CHANGE` |
| C | Policy tightened | original `ALLOW`, replay `DENY`, impact `MATERIAL_CHANGE` |
| D | Evidence stale | original `ALLOW`, replay `DENY`, impact `MATERIAL_CHANGE` |
| E | No change | original `ALLOW`, replay `ALLOW`, impact `UNCHANGED` |
| F | Exec not observed | admissibility `ALLOW`, execution authority `NOT_CHECKED` |

## Canonicalization and hashing

- Canonical JSON: `json.dumps(value, sort_keys=True, separators=(",", ":"))`.
- Hash scope (top-level fields): `schema_version`, `trace_id`, `scenario_id`,
  `action`, `state_change`, `original`, `replay`, `impact`,
  `execution_authority`, `verification`.
- The `trace_integrity` envelope is **excluded** from its own hash.
- Canonicalization is order-independent at the object level: reordering keys
  does not change the hash. This is asserted in
  `tests/test_trace_integrity.py::test_key_order_does_not_change_hash`.
- The scope is enumerated in the order above for readability. The hash itself
  is computed over a key-sorted serialization, so scope ordering does not
  affect the digest.
- SHA-256 establishes content integrity relative to the hashed scope. It does
  **not** establish truth, signer identity, completeness of real-world events,
  external timestamp authenticity, or hardware-rooted trust.

## macOS setup

From the project root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
Run tests

From the project root, with the virtual environment active:

bash
pytest -q
Expected: all tests pass. Counts by file:

File	Tests
tests/test_policy_engine.py	5
tests/test_replay_engine.py	3
tests/test_impact_analysis.py	5
tests/test_execution_authority.py	4
tests/test_trace_integrity.py	6
tests/test_scenarios.py	7
Total	30 passed
Launch the app

bash
streamlit run app.py
Then open the printed local URL (typically http://localhost:8501).

Honest limitations

All actors, actions, policies, and evidence are synthetic.
Replay is a deterministic comparison under declared inputs.
Replay cannot independently prove the original action actually executed.
A hash establishes integrity relative to the hashed content, not truth or
independent authenticity.
Execution-time authorization is not established unless the relevant
observation and verification mechanism are explicitly supplied.
A synthetic execution-authority observation is not hardware-backed or
independently trusted enforcement.
No alternate execution paths are proven covered. Conversely, this demo does
not prove that alternate execution paths are uncovered; it simply makes no
claim about coverage.
No real action is executed, authorized, blocked, or rolled back.
No Certor private implementation, API, or proprietary information is assumed.
No production readiness, certification, or security assurance is claimed.
Operator guide

1. Exact macOS setup commands (from project root)

bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
2. Exact command to run the full test suite

bash
pytest -q
3. Expected test results

All tests pass. Counts by file:

text
tests/test_policy_engine.py ......... 5 passed
tests/test_replay_engine.py ......... 3 passed
tests/test_impact_analysis.py ....... 5 passed
tests/test_execution_authority.py ... 4 passed
tests/test_trace_integrity.py ....... 6 passed
tests/test_scenarios.py ............. 7 passed
Total: 30 passed
4. Exact command to launch the local app

bash
streamlit run app.py
5. Walkthrough of the six scenarios

A — Baseline. Original decision ALLOW. No replay is performed. Use this
to show the happy path and the recorded inputs.

B — Authority revoked. Original decision ALLOW. Replay under REVOKED
authority yields DENY. Impact classification is MATERIAL_CHANGE. The
changed field is authority.state. The original decision is not rewritten.
Note in the UI that replay does not prove the original action was blocked
in production.

C — Policy tightened. Original ALLOW under policy 1.0. Replay under
policy 2.0 (rule release-tightened with on_match=DENY) yields DENY.
Changed fields include policy.version.

D — Evidence stale. Original ALLOW at evaluation_seq=105 with evidence
captured at seq 100 and max_age_seq=10. Replay at evaluation_seq=130 uses
the same evidence reference; the freshness rule marks it stale; decision
becomes DENY. Changed field: evidence.fresh_at_evaluation.

E — No change. Original ALLOW, replay ALLOW, impact UNCHANGED. This
proves the impact analyzer does not invent a change when none exists.

F — Exec not observed. Admissibility ALLOW. Execution-authority panel
shows NOT_CHECKED. The sidebar exposes an optional synthetic
execution-authority observation toggle that can be attached to any scenario
to exercise the separate OBSERVED_ALLOW path. The UI labels the observation
as synthetic.

6. Sample JSON trace (abridged, canonical form)

json
{
  "schema_version": "decisionassure.boundary-replay-lab/1.0",
  "trace_id": "trace-B_authority_revoked-3f1c2a0b9d4e",
  "scenario_id": "B_authority_revoked",
  "action": {"action_id": "release_funds", "parameters": {"amount": 2500, "currency": "USD", "payee": "synthetic-vendor-001"}},
  "state_change": {"change_id": "chg-authority-revoke", "kind": "AUTHORITY_STATE", "description": "...", "applied_at_seq": 140},
  "original": {
    "decision": "ALLOW",
    "reason_codes": ["AUTHORITY_VALID", "EVIDENCE_FRESH", "POLICY_RULE_MATCH_ALLOW"],
    "matched_rule_id": "release-default",
    "explanation": "Rule 'release-default' matched action 'release_funds' under policy treasury.release@1.0.",
    "inputs": {
      "policy": {"policy_id": "treasury.release", "version": "1.0"},
      "authority": {"subject_id": "agent-treasury-01", "state": "VALID", "source": "synthetic"},
      "evidence": [{"evidence_id": "ev-balance", "captured_at_seq": 100, "max_age_seq": 10, "source": "synthetic", "is_fresh_at_evaluation": true}],
      "evaluation_seq": 105
    }
  },
  "replay": {
    "decision": "DENY",
    "reason_codes": ["AUTHORITY_REVOKED"],
    "matched_rule_id": "release-default",
    "explanation": "Rule 'release-default' matched action 'release_funds' under policy treasury.release@1.0.",
    "inputs": {
      "policy": {"policy_id": "treasury.release", "version": "1.0"},
      "authority": {"subject_id": "agent-treasury-01", "state": "REVOKED", "source": "synthetic"},
      "evidence": [{"evidence_id": "ev-balance", "captured_at_seq": 100, "max_age_seq": 10, "source": "synthetic", "is_fresh_at_evaluation": false}],
      "evaluation_seq": 145
    }
  },
  "impact": {
    "classification": "MATERIAL_CHANGE",
    "reason_codes": ["IMPACT_MATERIAL_CHANGE"],
    "explanation": "At least one material governance input changed between original and replay. See findings for the exact fields.",
    "findings": [
      {"field_path": "policy.version", "original_value": "treasury.release@1.0", "replayed_value": "treasury.release@1.0", "changed": false, "note": "Policy identifier and version used for each evaluation."},
      {"field_path": "authority.state", "original_value": "VALID", "replayed_value": "REVOKED", "changed": true, "note": "Policy-relevant authority state at evaluation time."},
      {"field_path": "evidence.fresh_at_evaluation", "original_value": true, "replayed_value": false, "changed": true, "note": "Whether every evidence reference was fresh under its own evaluation_seq."},
      {"field_path": "evaluation_seq", "original_value": 105, "replayed_value": 145, "changed": true, "note": "Logical sequence used for freshness and audit ordering."},
      {"field_path": "decision", "original_value": "ALLOW", "replayed_value": "DENY", "changed": true, "note": "Admissibility decision produced by the policy engine."}
    ]
  },
  "execution_authority": {
    "status": "NOT_CHECKED",
    "reason_codes": ["EXEC_AUTH_NOT_CHECKED"],
    "explanation": "No execution-time authority observation was supplied. Execution authority is NOT_CHECKED. This is not a denial and not an approval.",
    "observation": null
  },
  "verification": {
    "notes": ["Synthetic data only. ...", "Replay is a deterministic comparison under declared inputs.", "..."],
    "disclaimer": "Illustrative local reference demo. Not a security product. Not an integration with Certor. ..."
  },
  "trace_integrity": {
    "algorithm": "sha256",
    "canonicalization": "json.dumps(sort_keys=True, separators=(',',':')) over the selected top-level fields listed in hash_scope.",
    "hash_scope": ["schema_version", "trace_id", "scenario_id", "action", "state_change", "original", "replay", "impact", "execution_authority", "verification"],
    "trace_hash": "<sha256 hex digest of the canonicalized hash scope; recompute per run>",
    "notes": ["The trace_integrity envelope is excluded from its own hash.", "..."]
  }
}
The trace_hash value is intentionally shown as a placeholder. It is
recomputed at runtime over the exact canonicalized hash scope and stored in
the exported trace. Because trace_id includes a per-run UUID suffix, the
digest differs across runs even when the scenario is identical. To inspect a
concrete digest, run the app, click Run original evaluation, and copy the
value from the TRACE INTEGRITY panel or from the downloaded JSON.
7. Sample human-readable report (abridged)

markdown
# DecisionAssure Boundary Replay Lab — Report

**Trace ID:** `trace-B_authority_revoked-3f1c2a0b9d4e`
**Scenario:** `B_authority_revoked`
**Schema:** `decisionassure.boundary-replay-lab/1.0`

## Action
- **Action ID:** release_funds
- **Parameters:** {'amount': 2500, 'currency': 'USD', 'payee': 'synthetic-vendor-001'}

## ORIGINAL ADMISSIBILITY
- **Decision:** ALLOW
- **Reason codes:** AUTHORITY_VALID, EVIDENCE_FRESH, POLICY_RULE_MATCH_ALLOW
- ...

## REPLAYED ADMISSIBILITY
- **Decision:** DENY
- **Reason codes:** AUTHORITY_REVOKED
- ...

## GOVERNANCE IMPACT
- **Classification:** MATERIAL_CHANGE
- ...

## EXECUTION AUTHORITY
- **Status:** NOT_CHECKED
- ...

## TRACE INTEGRITY
- **Algorithm:** sha256
- ...

## LIMITATIONS
- Synthetic data only. ...
8. Troubleshooting

ModuleNotFoundError: No module named 'src'
You are running Python from a different directory. Always run
streamlit run app.py and pytest from the project root, and ensure the
sys.path insertion in app.py runs (it does when launched from the project
root).

ModuleNotFoundError: No module named 'tests' when running app.py
app.py inserts the project root onto sys.path before importing
tests.conftest. Make sure tests/__init__.py exists (it does) and that you
launched from the project root.

pytest collects nothing
Run pytest from the project root. There is no pytest.ini; default discovery
finds tests/test_*.py.

streamlit: command not found
Activate the virtual environment: source .venv/bin/activate, then
pip install -r requirements.txt.

Python 3.10 errors on tuple[str, ...]
This project targets Python 3.11+. Install python3.11
(e.g., via brew install python@3.11).

JSON fixtures malformed
The loader in tests/conftest.py raises a clear error if
fixtures/scenarios.json is not valid JSON. Re-copy the file exactly.

9. Final checklist (clean environment)

□ python3.11 --version reports 3.11 or newer.
□ .venv created and activated.
□ pip install -r requirements.txt succeeds.
□ pytest -q reports 30 passed.
□ streamlit run app.py opens a browser tab at http://localhost:8501.
□ Sidebar lists all six scenarios.
□ Scenario A: original ALLOW; no replay.
□ Scenario B: original ALLOW, replay DENY, impact MATERIAL_CHANGE.
□ Scenario C: policy.version appears in changed fields.
□ Scenario D: evidence.fresh_at_evaluation appears in changed fields.
□ Scenario E: impact UNCHANGED.
□ Scenario F: execution authority NOT_CHECKED.
□ After running any scenario, the TRACE INTEGRITY panel shows
Trace integrity verified.
□ The downloaded JSON trace, when re-verified by the same in-app verifier,
reports valid: true with no findings.
□ Both the UI and the README state the limitations equivalently.
