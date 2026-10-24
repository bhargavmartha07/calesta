import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPORT_DIR = Path("reports")
LOG_DIR = Path("logs")
REPORT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

run_id = f"failure-{uuid.uuid4().hex[:12]}"
events = []
completed_steps = []

def now():
    return datetime.now(timezone.utc).isoformat()

def record(event, **details):
    entry = {
        "timestamp": now(),
        "run_id": run_id,
        "event": event,
        **details,
    }
    events.append(entry)
    print(json.dumps(entry))

for step in range(1, 11):
    if step == 7:
        record(
            "step_failed",
            step=step,
            reason="Deliberate simulated failure",
            recovery_action="resume_from_step_8",
        )
        break

    completed_steps.append(step)
    record("step_completed", step=step)

record(
    "recovery_started",
    action="resume_from_step_8",
    completed_steps=completed_steps,
)

for step in range(8, 11):
    completed_steps.append(step)
    record("step_completed", step=step, recovered=True)

record(
    "workflow_completed",
    status="succeeded",
    completed_steps=completed_steps,
    failed_step=7,
    recovery_action="resume_from_step_8",
)

with (LOG_DIR / "failure_trace.jsonl").open("w", encoding="utf-8") as f:
    for event in events:
        f.write(json.dumps(event) + "\n")

failure_policy = {
    "policy_name": "resume_after_simulated_step_failure",
    "failure_step": 7,
    "failure_type": "simulated",
    "recovery_action": "resume_from_step_8",
    "completed_steps_before_failure": list(range(1, 7)),
    "steps_after_recovery": [8, 9, 10],
    "final_status": "succeeded",
    "limitations": [
        "This is a controller-level simulation.",
        "It does not demonstrate recovery of a real Celesto guest process or persisted guest state."
    ]
}

(REPORT_DIR / "failure_policy.json").write_text(
    json.dumps(failure_policy, indent=2) + "\n",
    encoding="utf-8",
)

print("\nPASS: simulated step-7 failure and recovery trace recorded.")
