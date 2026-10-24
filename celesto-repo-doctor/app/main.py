
import os
import re
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ledger:ledger@localhost:5432/ledger",
)

SANDBOX_PATTERN = re.compile(r"^sbx-[a-z0-9]{8,}$")

VALID_STATES = {
    "created",
    "ready",
    "running",
    "succeeded",
    "failed",
    "deleted",
}


ALLOWED_TRANSITIONS = {
    "created": {"ready", "running", "failed", "deleted"},
    "ready": {"running", "failed", "deleted"},
    "running": {"succeeded", "failed"},
    "succeeded": {"deleted"},
    "failed": {"deleted"},
    "deleted": set(),
}


def get_connection():
    return psycopg.connect(DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The database schema will be initialized by PostgreSQL's seed SQL.
    yield


app = FastAPI(
    title="Celesto Run Ledger",
    description="Tracks AI agent runs executed in Celesto sandboxes.",
    lifespan=lifespan,
)


class RunCreate(BaseModel):
    run_id: str = Field(min_length=1)
    sandbox_name: str
    problem_id: str = Field(min_length=1)
    state: str
    execution_target: str


def validate_run(run: RunCreate):
    if not SANDBOX_PATTERN.fullmatch(run.sandbox_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid sandbox name",
        )

    if run.state not in VALID_STATES:
        raise HTTPException(
            status_code=400,
            detail="Invalid run state",
        )

    if run.execution_target != "celesto_sandbox":
        raise HTTPException(
            status_code=400,
            detail="Execution target must be celesto_sandbox",
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/runs")
def list_runs():
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT run_id, sandbox_name, problem_id,
                       state, execution_target
                FROM runs
                ORDER BY run_id
                """
            ).fetchall()

        return [
            {
                "run_id": row[0],
                "sandbox_name": row[1],
                "problem_id": row[2],
                "state": row[3],
                "execution_target": row[4],
            }
            for row in rows
        ]
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Run ledger database unavailable",
        ) from exc


@app.post("/api/runs", status_code=201)
def create_run(run: RunCreate):
    validate_run(run)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, sandbox_name, problem_id,
                    state, execution_target
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    run.run_id,
                    run.sandbox_name,
                    run.problem_id,
                    run.state,
                    run.execution_target,
                ),
            )

        return run.model_dump()

    except psycopg.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Run ID or sandbox name already exists",
        ) from exc

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not write to run ledger",
        ) from exc



@app.patch("/api/runs/{run_id}/state")
def update_run_state(run_id: str, state: str):
    if state not in VALID_STATES:
        raise HTTPException(
            status_code=400,
            detail="Invalid run state",
        )

    try:
        with get_connection() as conn:
            # Lock the row so concurrent updates cannot race.
            cursor = conn.execute(
                """
                SELECT run_id, sandbox_name, problem_id,
                       state, execution_target
                FROM runs
                WHERE run_id = %s
                FOR UPDATE
                """,
                (run_id,),
            )
            row = cursor.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Run not found",
                )

            current_state = row[3]

            if state != current_state and state not in ALLOWED_TRANSITIONS[current_state]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Invalid state transition: {current_state} -> {state}",
                )

            cursor = conn.execute(
                """
                UPDATE runs
                SET state = %s
                WHERE run_id = %s
                RETURNING run_id, sandbox_name, problem_id,
                          state, execution_target
                """,
                (state, run_id),
            )
            updated = cursor.fetchone()

        return {
            "run_id": updated[0],
            "sandbox_name": updated[1],
            "problem_id": updated[2],
            "state": updated[3],
            "execution_target": updated[4],
        }

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not update run ledger",
        ) from exc
