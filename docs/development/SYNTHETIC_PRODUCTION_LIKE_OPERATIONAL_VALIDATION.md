# Synthetic production-like operational validation

Status: **Authorized for generated pre-production validation only.**

The validation harness exercises `synthetic-reference-erp-v1@1.0.0` without changing
its demo authority. It reads only the checksum-bound generated package, opens no
network connection, accepts no credential or caller path, and always reports
`production_ready=false`.

Profiles:

| Profile | Purpose | Bound workload |
|---|---|---|
| `baseline` | repeated happy-path extraction | 10 complete generated reads, page <=100 |
| `resilience` | safe failure classification | drift, timeout, throttle and credential rejection |
| `soak` | deterministic local repetition/pagination | 250 complete reads, page size 5 |

Run with:

```powershell
.\.venv\Scripts\python.exe scripts\run_synthetic_operational_validation.py baseline
.\.venv\Scripts\python.exe scripts\run_synthetic_operational_validation.py resilience
.\.venv\Scripts\python.exe scripts\run_synthetic_operational_validation.py soak
```

Reports contain only package/profile identity, safe limits, durations, counts and
closed outcome codes. They contain no source keys, record values, credentials,
endpoints or paths. Runtime duration limits are deliberately broad local-regression
guards, not production SLOs.

This milestone validates the adapter boundary, not PostgreSQL service throughput,
external transport, real scale, production capacity, RPO/RTO or real ERP behavior.
Those remain blocked until an approved real-source package exists.
