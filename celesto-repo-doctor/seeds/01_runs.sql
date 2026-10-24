
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    sandbox_name TEXT NOT NULL UNIQUE,
    problem_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK (
        state IN (
            'created',
            'ready',
            'running',
            'succeeded',
            'failed',
            'deleted'
        )
    ),
    execution_target TEXT NOT NULL CHECK (
        execution_target = 'celesto_sandbox'
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO runs (
    run_id,
    sandbox_name,
    problem_id,
    state,
    execution_target
)
VALUES (
    'seed-run-001',
    'sbx-seeddemo1',
    'repository-doctor',
    'deleted',
    'celesto_sandbox'
)
ON CONFLICT DO NOTHING;
