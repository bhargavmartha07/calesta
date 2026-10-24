import uuid

import requests

BASE_URL = "http://localhost:8080"


def create_test_run(prefix):
    suffix = uuid.uuid4().hex[:12]
    run_id = f"pytest-{prefix}-{suffix}"
    sandbox_name = f"sbx-pytest{prefix}{suffix}"

    response = requests.post(
        f"{BASE_URL}/api/runs",
        json={
            "run_id": run_id,
            "sandbox_name": sandbox_name,
            "problem_id": "repository-doctor",
            "state": "created",
            "execution_target": "celesto_sandbox",
        },
        timeout=10,
    )

    assert response.status_code == 201, response.text
    return run_id


def test_created_to_running_is_allowed():
    run_id = create_test_run("valid")

    response = requests.patch(
        f"{BASE_URL}/api/runs/{run_id}/state",
        params={"state": "running"},
        timeout=10,
    )

    assert response.status_code == 200, response.text
    assert response.json()["state"] == "running"


def test_running_to_deleted_is_rejected():
    run_id = create_test_run("invalid")

    response = requests.patch(
        f"{BASE_URL}/api/runs/{run_id}/state",
        params={"state": "running"},
        timeout=10,
    )
    assert response.status_code == 200, response.text

    response = requests.patch(
        f"{BASE_URL}/api/runs/{run_id}/state",
        params={"state": "deleted"},
        timeout=10,
    )

    assert response.status_code == 409, response.text
    assert "Invalid state transition" in response.text


def test_unknown_run_returns_404():
    run_id = f"pytest-missing-{uuid.uuid4().hex[:12]}"

    response = requests.patch(
        f"{BASE_URL}/api/runs/{run_id}/state",
        params={"state": "running"},
        timeout=10,
    )

    assert response.status_code == 404, response.text
