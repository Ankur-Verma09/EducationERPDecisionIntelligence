# Docker Development and Phase 1 Validation Runbook

## Purpose

This runbook documents how to authorize Docker Desktop, start and stop the local
stack, run PostgreSQL migrations and tests, scan the application image, perform the
container smoke test, and resolve the failures encountered during Phase 1 validation.

Run the commands from Windows PowerShell in:

```powershell
Set-Location E:\EducationERPDecisionIntelligence
```

## 1. Docker Desktop authorization

Docker Desktop must be running, and the executing Windows account must be a member
of `docker-users`.

Check membership and engine access:

```powershell
whoami
whoami /groups | findstr docker-users
docker info
```

If the account is missing, run elevated PowerShell:

```powershell
Add-LocalGroupMember `
    -Group docker-users `
    -Member 'DESKTOP-00B7QTS\CodexSandboxOnline'
```

Sign out and back in so Windows creates a new security token. Fully quit and restart
Docker Desktop after changing group membership.

Docker Desktop engine pipes may still be limited to the interactive account that
launched Docker Desktop. If `CodexSandboxOnline` receives pipe access denied while
`Ankur` can run `docker info`, execute Docker validation from the `Ankur` terminal.
Do not expose an unauthenticated Docker daemon on TCP port 2375.

## 2. Start the database only

```powershell
docker compose up -d database
docker compose ps
```

Wait until PostgreSQL is healthy:

```powershell
do {
    Start-Sleep -Seconds 2
    $health = docker inspect `
        --format '{{.State.Health.Status}}' `
        educationerpdecisionintelligence-database-1 2>$null
    Write-Host "PostgreSQL health: $health"
} until ($health -eq 'healthy')
```

## 3. Run the migration lifecycle

```powershell
$env:EDUERP_ENVIRONMENT = 'test'
$env:EDUERP_DATABASE_URL = `
    'postgresql+psycopg://education_erp:local-only@localhost:5432/education_erp'
$env:EDUERP_TEST_DATABASE_URL = $env:EDUERP_DATABASE_URL

.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic downgrade base
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current 2>&1
```

The expected final revision is `0001 (head)`.

Alembic writes normal informational output to stderr. Windows PowerShell 5 may
display this as `NativeCommandError` even when the command succeeds. Use
`$LASTEXITCODE`; zero means success.

## 4. Run the complete PostgreSQL test suite

Keep `EDUERP_TEST_DATABASE_URL` set and run the complete suite:

```powershell
.\.venv\Scripts\python.exe -m pytest
$LASTEXITCODE
```

Do not run only `tests\integration\test_database.py` without disabling the global
coverage gate. The tests can all pass while the command fails because one file alone
cannot meet the repository-wide 90% coverage requirement.

The verified Phase 1 result is 32 passed, no skips, and 95.18% coverage.

## 5. Build the images

```powershell
docker compose build --no-cache api migrate
$LASTEXITCODE
```

The runtime uses `python:3.11-alpine`. The earlier Debian slim image contained four
critical `perl-base` vulnerabilities without an available Debian fix.

## 6. Scan the application image

```powershell
docker run --rm `
    -v /var/run/docker.sock:/var/run/docker.sock `
    aquasec/trivy:0.58.2 `
    image --exit-code 1 --severity CRITICAL `
    educationerpdecisionintelligence-api

$LASTEXITCODE
```

Expected result:

```text
Total: 0 (CRITICAL: 0)
```

The first scan downloads the Trivy vulnerability database and may take several
minutes. Informational messages written to stderr can appear as PowerShell
`NativeCommandError`; the final process exit code determines success.

## 7. Start the complete stack

```powershell
docker compose up -d
docker compose ps
```

Compose starts PostgreSQL, runs the one-shot migration service, and then starts the
API. Expected state:

- `database`: healthy
- `migrate`: exited successfully
- `api`: healthy

## 8. Run the container smoke test

```powershell
$ready = $false

foreach ($attempt in 1..30) {
    try {
        $response = Invoke-RestMethod `
            http://localhost:8000/api/v1/health/ready `
            -TimeoutSec 3

        if ($response.status -eq 'ok') {
            $ready = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    docker compose logs --no-color api migrate database
    throw 'Container readiness smoke test failed'
}

Invoke-RestMethod http://localhost:8000/api/v1/health/live
Invoke-RestMethod http://localhost:8000/api/v1/health/ready
```

Both endpoints must return `status: ok`.

## 9. View status and logs

```powershell
docker compose ps
docker compose logs --no-color api migrate database
docker compose logs --follow api
```

Press `Ctrl+C` to stop following logs; it does not stop the containers.

## 10. Stop or reset Docker resources

Stop and remove project containers and network while preserving PostgreSQL data:

```powershell
docker compose down
```

Stop without removing containers:

```powershell
docker compose stop
```

Restart stopped services:

```powershell
docker compose start
```

Delete the PostgreSQL volume only when an intentional clean database reset is
required. This permanently removes local database contents:

```powershell
docker compose down --volumes
```

## Problems encountered and solutions

### Docker engine pipe returns access denied

Symptoms:

```text
open //./pipe/docker_engine: Access is denied
```

Resolution:

1. Add the executing account to `docker-users`.
2. Sign out and back in.
3. Fully restart Docker Desktop.
4. If Docker Desktop's per-user pipe still excludes the sandbox account, run the
   Docker commands from the account that launched Docker Desktop.

### Global Python has no pip and `_distutils_hack` fails

Use the isolated project interpreter instead of global Python:

```powershell
.\.venv\Scripts\python.exe -m pip --version
```

All project Python commands should use `.\.venv\Scripts\python.exe`.

### `allowed_hosts` fails JSON parsing in the container

Symptom:

```text
SettingsError: error parsing value for field "allowed_hosts"
```

Cause: `pydantic-settings` attempted automatic JSON decoding before the
comma-separated validator ran.

Resolution: `allowed_hosts` uses `NoDecode`, and a regression test verifies:

```text
EDUERP_ALLOWED_HOSTS=localhost,127.0.0.1,api
```

### Targeted PostgreSQL tests pass but pytest exits 1

Cause: the global coverage configuration applies to a targeted test file, which
cannot cover the whole application.

Resolution: run the complete suite with `EDUERP_TEST_DATABASE_URL` set.

### Trivy finds critical Debian `perl-base` vulnerabilities

Cause: inherited packages in `python:3.11-slim`.

Resolution: use the Alpine Python runtime and rebuild without cache. The verified
Alpine scan reports zero critical vulnerabilities.

### Docker and Alembic output appears as `NativeCommandError`

Docker Compose and Alembic commonly write progress/information to stderr. Windows
PowerShell 5 wraps stderr as an error record. Confirm actual success with:

```powershell
$LASTEXITCODE
```

Zero is success. Nonzero requires investigation.

## Recommended evidence capture

```powershell
Start-Transcript `
    -Path E:\EducationERPDecisionIntelligence\phase1-docker-validation.log `
    -Force

# Run validation commands.

Stop-Transcript
```
