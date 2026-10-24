# Celesto Repository Doctor

## Problem statement

This project runs repository diagnostic commands inside a Celesto Cloud computer and records execution results in a FastAPI control plane backed by PostgreSQL.

The goal is to evaluate remote execution, safety checks, persistence, lifecycle behavior, reliability, failure recovery, and concurrency without claiming capabilities that have not been verified.

## How I used Celesto

- Used Celesto Cloud to execute diagnostic commands in an Ubuntu 24.04 computer.
- Verified successful remote command execution.
- Verified that `/tmp/fixture.txt` survived a stop/start cycle and retained its expected SHA-256 hash:
  `2bc9c43e0547e59778a9c0ee00afb82f33009ab07b0694657a964282d50c15c6`
- Implemented a pre-execution safety hook that blocks selected dangerous command patterns before invoking the Celesto CLI.
- Tested the safety hook using automated tests with a mocked CLI.
- Attempted snapshot listing and creation. Listing succeeded but returned no snapshots; creation failed with a computer-not-found error even though the computer remained visible through computer lookup.

The worker currently reuses an existing cloud computer. It does not yet demonstrate the complete create-use-delete lifecycle for a newly created computer.

## Architecture

- **FastAPI:** exposes health and run-management endpoints.
- **PostgreSQL:** stores the run ledger.
- **Worker:** submits run records, invokes Celesto commands, records results, and updates run states.
- **Celesto Cloud:** executes diagnostic commands outside the host environment.
- **Reports and logs:** preserve test results and evaluation evidence.

The command safety hook is a limited heuristic, not a comprehensive security boundary. The mocked test does not prove protection against every attack technique.

## Eval report

The evaluation is incomplete.

- Two successful worker runs have been recorded, both reusing an existing cloud computer.
- Zero fresh-sandbox evaluation runs have been verified.
- The required 20 fresh-sandbox runs have not been completed.
- Five-job concurrency has not been demonstrated.
- Median and p90 wall-clock time, median boot-to-ready time, and total cost have not been fully measured.
- Step-7 failure and resume behavior are demonstrated by a controller-level simulation, not recovery of a real guest process.

See `reports/reliability.json`, `reports/concurrency.json`, `reports/failure_policy.json`, and `reports/failure_trace.jsonl`.

## Containment test

The tested command `rm -rf /` was blocked by the worker safety hook before the Celesto CLI was called. The test asserts that the mocked CLI was not invoked.

The test did not execute the destructive command. The evidence supports blocking of this specific test input, not comprehensive containment or an independent audit of host integrity.

See `reports/containment.json` and `tests/test_safety_hook.py`.

## State and failure design

Run state is recorded in PostgreSQL. The worker updates run states and writes command results to JSON Lines logs. The current worker reuses a pre-existing computer and deliberately does not delete a computer it does not own.

The step-7 failure demonstration resumes at step 8 in a controller-level simulation. Real guest-process recovery remains unverified.

Snapshot creation was attempted with Celesto CLI versions 0.1.4 and 0.1.6 but failed with a computer-not-found error. The computer remained visible through `celesto computer get` and `celesto computer list --cloud`. The root cause is unknown.

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.12 or a compatible environment for the API and worker
- A Celesto account and authenticated Celesto CLI for cloud execution

### Configure environment

Copy `.env.example` to `.env` and fill in the required values locally. Do not commit `.env` or API keys.

### Start the control plane

```bash
docker compose up --build -d
```

Check the health endpoint:

```bash
curl http://localhost:8080/health
```

Expected response:

```json
{"status":"ok"}
```

List recorded runs:

```bash
curl http://localhost:8080/api/runs
```

### Run the worker

Authenticate the Celesto CLI in the environment where the worker runs. Confirm that the configured computer ID is accessible before running the worker.

From the project root, with the appropriate Python environment activated:

```bash
python worker.py
```

The current worker uses an existing computer ID configured in `worker.py`; review that value before running it. This version is a diagnostic prototype, not a complete fresh-sandbox lifecycle evaluator.

### Run tests

```bash
python -m pytest -v tests
```

## Project evidence

- `reports/`: evaluation reports, limitations, and postmortem.
- `logs/commands.jsonl`: worker command and lifecycle events.
- `tests/`: automated report and safety-hook tests.
- `failure_demo.py`: controller-level failure simulation.

## Known limitations and next steps

1. Complete at least 20 end-to-end runs on fresh sandboxes and report the required metrics.
2. Demonstrate five or more concurrent jobs with unique sandbox names.
3. Verify fresh computer creation and cleanup on success, failure, and interruption.
4. Investigate the snapshot lookup failure and verify another Celesto capability.
5. Strengthen containment testing and distinguish mocked tests from real guest tests.
6. Finish the short demo video and verify every required deliverable.
7. Publish the repository and review the final evidence.

All results should be reported with their actual test scope and limitations.
