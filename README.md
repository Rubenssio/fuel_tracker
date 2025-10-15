# Fuel Tracker Bootstrap Service

This repository contains a minimal Django application packaged for local development with Docker Compose. The service runs
against a PostgreSQL database, runs migrations on startup, seeds a sentinel record, and exposes a dynamic health endpoint.

## Running locally

```bash
# one-time
./scripts/bootstrap-env.sh
# then
docker compose up --build
```

The `.env` file is local-only and ignored by git. Refer to `.env.example` for the required environment variables.

After the stack is up, verify the service:
   - http://localhost:8000/ returns the plain text `success` response.
   - http://localhost:8000/health returns JSON such as
     ```json
     {"status":"ok","db":{"connected":true,"migrated":true,"seeded":true}}
     ```

Stopping the containers (`Ctrl+C`) and re-running the command will reuse the named PostgreSQL volume, keeping the seeded data.
