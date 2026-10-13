"""DecisionAssure Boundary Replay Lab — Streamlit UI.

Runs locally. Synthetic data only. No outbound network calls. No telemetry.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.execution_authority import evaluate as eval_exec  # noqa: E402
from src.impact_analysis import analyze  # noqa: E402
from src.models import ExecutionAuthorityObservation  # noqa: E402
from src.replay_engine import run_original, run_replay  # noqa: E402
from src.report_generator import generate_report  # noqa: E402
from src.trace_builder import build_trace  # noqa: E402
from src.trace_integrity import canonical_dumps, verify_trace  # noqa: E402

sys.path.insert(0, str(ROOT / "tests"))
from tests.conftest import load_scenarios  # noqa: E402

st.set_page_config(
    page_title="DecisionAssure Boundary Replay Lab",
    layout="wide",
)

st.title("DecisionAssure Boundary Replay Lab")
st.caption(
    "Admissibility after change ≠ Current authority at execution. "
    "Synthetic, deterministic, local demonstration."
)

SCENARIOS = load_scenarios()
SCENARIOS_BY_ID = {s.scenario_id: s for s in SCENARIOS}

with st.sidebar:
    st.header("Scenario")
    scenario_id = st.radio(
        "Select scenario",
        options=list(SCENARIOS_BY_ID.keys()),
        format_func=lambda k: f"{k} — {SCENARIOS_BY_ID[k].title}",
    )
    st.markdown("---")
    st.markdown(
        "**Synthetic execution-authority observation**\n\n"
        "Optional fixture to exercise the separate execution-authority path. "
        "This is a supplied synthetic observation, not hardware-rooted proof."
    )
    include_synthetic_obs = st.checkbox(
        "Attach synthetic execution-authority observation (ALLOW)",
        value=False,
    )

scenario = SCENARIOS_BY_ID[scenario_id]

st.subheader(scenario.title)
st.write(scenario.description)

run = st.button("Run original evaluation")
apply_and_replay = st.button("Apply governance change & replay")

if "trace" not in st.session_state:
    st.session_state["trace"] = None
if "verdict" not in st.session_state:
    st.session_state["verdict"] = None

if run or apply_and_replay:
    original = run_original(scenario)

    replay = None
    if apply_and_replay and scenario.replayed_inputs is not None:
        replay = run_replay(scenario)

    impact = analyze(original, replay)

    observation = None
    if include_synthetic_obs:
        observation = ExecutionAuthorityObservation(
            subject_id=scenario.original_inputs.authority.subject_id,
            action_id=scenario.action.action_id,
            observed_at_seq=scenario.original_inputs.evaluation_seq,
            status="ALLOW",
            observer="synthetic-observer",
            is_synthetic=True,
        )
    exec_result = eval_exec(observation)

    trace_id = f"trace-{scenario.scenario_id}-{uuid.uuid4().hex[:12]}"
    trace = build_trace(scenario, original, replay, impact, exec_result, trace_id)
    verdict = verify_trace(trace)

    st.session_state["trace"] = trace
    st.session_state["verdict"] = verdict

trace = st.session_state["trace"]
verdict = st.session_state["verdict"]

if trace is None:
    st.info("Select a scenario and click **Run original evaluation**.")
else:
    original_payload = trace["original"]
    replay_payload = trace.get("replay")
    impact_payload = trace["impact"]
    exec_payload = trace["execution_authority"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ORIGINAL ADMISSIBILITY")
        st.metric("Decision", original_payload["decision"])
        st.write("**Reason codes:**", ", ".join(original_payload["reason_codes"]))
        st.write(original_payload["explanation"])
        st.json(original_payload["inputs"], expanded=False)

    with col2:
        st.markdown("### REPLAYED ADMISSIBILITY")
        if replay_payload is None:
            st.write("_No replay was performed for this scenario._")
        else:
            st.metric("Decision", replay_payload["decision"])
            st.write("**Reason codes:**", ", ".join(replay_payload["reason_codes"]))
            st.write(replay_payload["explanation"])
            st.json(replay_payload["inputs"], expanded=False)

    st.markdown("### GOVERNANCE IMPACT")
    st.write(f"**Classification:** {impact_payload['classification']}")
    st.write(impact_payload["explanation"])
    if impact_payload["findings"]:
        st.table(
            [
                {
                    "Field": f["field_path"],
                    "Original": str(f["original_value"]),
                    "Replayed": str(f["replayed_value"]),
                    "Changed": f["changed"],
                    "Note": f["note"],
                }
                for f in impact_payload["findings"]
            ]
        )

    st.markdown("### EXECUTION AUTHORITY")
    st.write(f"**Status:** {exec_payload['status']}")
    st.write(exec_payload["explanation"])
    if exec_payload["observation"] is None:
        st.write("_No execution-authority observation was supplied._")
    else:
        st.json(exec_payload["observation"], expanded=False)
        st.warning(
            "The observation above is synthetic. It is not independently "
            "authenticated or hardware-rooted proof."
        )

    st.markdown("### TRACE INTEGRITY")
    if verdict and verdict["valid"]:
        st.success("Trace integrity verified.")
    else:
        st.error("Trace integrity verification failed.")
    if verdict:
        st.write("**Findings:**", verdict["findings"] or ["none"])
        st.write("**Recorded hash:**", verdict["recorded_hash"])
        st.write("**Recomputed hash:**", verdict["recomputed_hash"])

    st.markdown("### LIMITATIONS")
    for note in trace["verification"]["notes"]:
        st.markdown(f"- {note}")
    st.caption(trace["verification"]["disclaimer"])

    st.markdown("---")
    st.download_button(
        "Download JSON trace",
        data=canonical_dumps(trace).encode("utf-8"),
        file_name=f"{scenario.scenario_id}.trace.json",
        mime="application/json",
    )
    st.download_button(
        "Download human-readable report",
        data=generate_report(trace).encode("utf-8"),
        file_name=f"{scenario.scenario_id}.report.md",
        mime="text/markdown",
    )

    with st.expander("Raw trace JSON"):
        st.code(json.dumps(trace, indent=2, sort_keys=True), language="json")