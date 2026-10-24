import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(filename):
    path = REPORTS / filename
    assert path.is_file(), f"Missing report: {filename}"
    return json.loads(path.read_text(encoding="utf-8-sig"))


def test_containment_report_records_blocking():
    report = load_json("containment.json")

    assert report["status"] == "passed"
    assert report["evidence"]["blocked_by_safety_hook"] is True
    assert report["evidence"]["celesto_cli_called"] is False
    assert report["deliberate_misbehavior"]["executed"] is False


def test_failure_policy_records_step_seven():
    report = load_json("failure_policy.json")

    assert report["failure_step"] == 7
    assert report["failure_type"] == "simulated"
    assert report["recovery_action"] == "resume_from_step_8"
    assert report["final_status"] == "succeeded"


def test_failure_trace_is_valid_jsonl():
    path = ROOT / "logs" / "failure_trace.jsonl"
    assert path.is_file(), "Missing failure_trace.jsonl"

    events = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]

    assert any(
        event.get("event") == "step_failed"
        and event.get("step") == 7
        for event in events
    )

    assert any(
        event.get("event") == "recovery_started"
        and event.get("action") == "resume_from_step_8"
        for event in events
    )

    assert any(
        event.get("event") == "workflow_completed"
        and event.get("status") == "succeeded"
        for event in events
    )


def test_worker_report_has_required_fields():
    report = load_json("worker_report.json")

    for field in (
        "run_id",
        "sandbox_name",
        "execution_target",
        "status",
    ):
        assert field in report, f"Missing worker report field: {field}"

    assert report["execution_target"] == "celesto_sandbox"
    assert report["status"] in ("succeeded", "failed")