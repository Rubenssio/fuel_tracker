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
To reset everything (including the database volume), run:

```bash
docker compose down -v
```

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
- Preferred UTC offset for display (whole-hour offsets from UTC, stored as `utc_offset_minutes`).

Saving the form refreshes the page with a preview showing sample values (100 km, 50 L, and a currency amount) rendered using the selected preferences. The stored data remains metric; conversions happen only for display. Timestamps are saved in UTC; the `utc_offset_minutes` preference will be used for future view-time conversions.

## Vehicles

Authenticated users can manage their vehicles from simple server-rendered pages:

- List all vehicles at http://localhost:8000/vehicles.
- Add a new vehicle at http://localhost:8000/vehicles/add.
- Edit or delete entries from the list view; deletes are CSRF-protected POST requests.

## Fill-Ups

Track refueling events for each vehicle with server-rendered forms at:

- Add a fill-up at http://localhost:8000/fillups/add.
- Edit or delete an existing fill-up via the vehicle list.

Each fill-up stores the odometer reading (kilometers only), volume (liters), and total amount (stored in the currency you enter).
Validation enforces that liters and total amount are greater than zero, odometer readings stay above zero, fill-up dates are not in the future,
and odometer readings remain strictly increasing for each vehicle when sorted by date and creation order.

## Database quick checks (while app is running)

Status and logs:

```
docker compose ps
docker compose logs -f web
```

PostgreSQL introspection helpers:

```
docker compose exec db psql -U app -d app
docker compose exec db psql -U app -d app -c '\dt'
docker compose exec db psql -U app -d app -c '\d accounts_user'
docker compose exec db psql -U app -d app -c '\d profiles_profile'
docker compose exec db psql -U app -d app -c '\d vehicles_vehicle'
```

Quick table samples:

```
docker compose exec db psql -U app -d app -c 'SELECT id, email, is_active, date_joined FROM accounts_user LIMIT 10;'
docker compose exec db psql -U app -d app -c 'SELECT id, user_id, display_name, currency, distance_unit, volume_unit, utc_offset_minutes FROM profiles_profile LIMIT 10;'
docker compose exec db psql -U app -d app -c 'SELECT id, user_id, name, make, model, year, fuel_type FROM vehicles_vehicle ORDER BY id DESC LIMIT 10;'
```

Django management helpers:

```
docker compose exec web python manage.py showmigrations
docker compose exec web python manage.py showmigrations accounts
docker compose exec web python manage.py showmigrations profiles
docker compose exec web python manage.py showmigrations vehicles
```
