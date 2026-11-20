# Assignment 10 — Cloud Operations Agent: Failed Deployment

Run with `python solution.py`. Both incidents include separate logs, deploy
history, and metrics. The database pool incident is WARN and automatically
executes the low-risk `restart_single_pod`. A rollback-class action remains an
approval request; an assertion verifies it is never auto-executed.

## Console output

```text
incident deploy-500: severity=CRITICAL; logs=2; deploys=2; metrics=2
  logs: ['health check failed after deploy', 'error rate exceeded threshold']
  deploy history: ['v1.7 healthy', 'v1.8 failed']
  metrics: {'error_rate': '18%', 'healthy_pods': 1}
action rollback_deployment: approval requested
incident db-pool-501: severity=WARN; logs=2; deploys=1; metrics=2
  logs: ['connection pool at maximum', 'requests queued for connections']
  deploy history: ['v2.3 healthy']
  metrics: {'pool_used': '100%', 'queue_depth': 12}
action restart_single_pod: executed automatically (low risk)
rollback auto-execution assertion: passed
```
