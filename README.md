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

## Auth

The service exposes minimal email-based authentication flows using server-rendered HTML forms:

- `GET /auth/signup` — create a new account.
- `POST /auth/signup` — submit the signup form; requires a unique email and a password that is at least 8 characters with at least one letter and one number.
- `GET/POST /auth/signin` — authenticate with email and password.
- `GET /auth/signout` — terminate the current session.

Manual test steps:
1. Visit `/auth/signup`, fill in the form, and submit. You should be redirected to `/` on success.
2. Visit `/auth/signout` to clear the session (redirects to `/`).
3. Visit `/auth/signin`, log in with the same credentials, and confirm the redirect back to `/`.
4. Try passwords that are too short or missing letters/numbers to see the validation errors.

## Profile settings

Authenticated users can manage their profile preferences at `/settings`. The page lets you update:

- Optional display name.
- Currency code label (3-letter ISO code, used for labelling values only).
- Preferred distance and volume units for viewing data.
- Timezone (IANA string such as `UTC`).

Saving the form refreshes the page with a preview showing sample values (100 km, 50 L, and a currency amount) rendered using the selected preferences. The stored data remains metric; conversions happen only for display.
