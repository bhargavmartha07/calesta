# Postmortem

## Summary

Automated tests (13/13) passed. The FastAPI control plane is healthy with PostgreSQL. The worker was updated to invoke the Celesto CLI via WSL; end-to-end guest execution against the existing cloud computer remains blocked due to provider state.

## What worked

- The Celesto CLI authenticated successfully (version 0.1.6).
- FastAPI health and API endpoints verified locally.
- All 13 project tests passed (API transitions, lifecycle guards, reports, safety hook).
- The worker rejected the tested destructive command before invoking the Celesto CLI.
- Ownership guard prevents deleting a pre-existing computer.
- Command history shows prior successful guest execution against cmp_aafb9b97334f.

## What did not complete

- Creating a new cloud computer previously returned HTTP 429. The cause has not been established.
- The existing cloud computer (cmp_aafb9b97334f) is reported as `starting` with `started_at: null` by the API; observability shows a runtime instance and guest metrics but API state has not reached `running`. Real guest execution could not be safely verified end-to-end at submission time.
- The required 20 end-to-end runs on fresh sandboxes have not been completed.
- The step-7 failure and recovery workflow is a controller-level simulation, not real guest recovery.
- Snapshot restoration, network policy enforcement, and concurrent Celesto jobs have not yet been verified.

## Safety and resource handling

The worker reused a pre-existing computer and does not own it. The dangerous command used in the safety-hook test was mocked and was not sent to the guest. No cloud resources were created or deleted during this submission work.

## Next actions

1. Resolve the cloud provisioning/start issue for cmp_aafb9b97334f with Celesto support (provide computer_id, timestamps, statuses, observability data). Do not repeatedly start/stop/restart.
2. Verify worker end-to-end once the computer reaches `running` or an alternative working target is available.
3. Implement and verify the required lifecycle and concurrency experiments.
4. Demonstrate additional Celesto capabilities with actual evidence.
5. Run the required 20 fresh-sandbox trials and compute metrics from recorded measurements.
