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
- Efficiency unit for displaying fuel consumption (choose L/100km or MPG; storage remains metric).
- Preferred UTC offset for display (whole-hour offsets from UTC, stored as `utc_offset_minutes`).

Saving the form refreshes the page with a preview showing sample values (100 km, 50 L, and a currency amount) rendered using the selected preferences. Efficiency output respects the efficiency unit only; distance and volume preferences continue to drive odometer, volume, per-distance cost, and per-volume price labels. The stored data remains metric; conversions happen only for display. Timestamps are saved in UTC; the `utc_offset_minutes` preference will be used for future view-time conversions.

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

Forms accept odometer and volume inputs in your selected units and convert them back to kilometers and liters before saving.

## History

Browse all fill-ups for the signed-in user at http://localhost:8000/history. Use query parameters to narrow results, for example:

- `/history?vehicle=3&start=2025-09-01&end=2025-10-19`
- `/history?brand=Shell&grade=Premium`
- `/history?station=Chevron&sort=total&dir=desc`

The History page shows per-fill derived values (distance since last, unit price, efficiency, cost per distance). Stored values remain metric; display converts to user preferences with rounding.
All derived values are computed at view time from canonical metric storage; units and rounding are display-only.

## Metrics

Review per-vehicle and aggregate performance at http://localhost:8000/metrics. The page supports filtering by vehicle and rolling window via query parameters, for example `/metrics?vehicle=all&window=30`.

All stored values remain metric; conversions happen at render time based on the profile preferences you set in `/settings`. Display rounding rules:

All derived values are computed at view time from canonical metric storage; units and rounding are display-only.

- Currency totals, per-distance costs, and unit prices: 2 decimal places.
- Volumes: 2 decimal places.
- Efficiency: 1 decimal place (`L/100km` in metric or `MPG` in imperial).
- Distances: whole numbers after conversion to the preferred unit.

## Statistics

Explore cost and efficiency trends at http://localhost:8000/statistics. The page offers vehicle and period selectors (30, 90, year-to-date, or all-time via `?window=all`) and shows:

- Summary cards for the selected window (rolling averages, totals, and per-distance costs).
- Inline SVG line charts for cost per volume and per-fill consumption.
- A brand/grade comparison table with average price, efficiency, and fill-up counts.

Values are calculated from canonical metric storage and converted to your preferred units at render time. Rounding matches the metrics page (currency and per-volume prices to 2 decimals, efficiency to 1 decimal, distances as whole numbers). When no data matches the filters, friendly “No data” messages are displayed instead of charts or tables.

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

## Observability

Inspect structured request logs streamed to stdout:

```
docker compose logs -f web | grep request_finished
```

Sample output:

```
ts=2024-04-10T18:42:13Z level=INFO logger=core.request cid=5f1d6fa85b0d4cb48c8128dbd3e59fa2 uid=1 method=GET path="/health" status=200 msg="request_finished"
```

Each HTTP response includes the `X-Request-ID` header. Capture it for downstream calls, or override it on inbound requests:

```
curl -i http://localhost:8000/ | grep -i x-request-id
```

Authentication audit events are persisted in `audit_authevent`:

```
docker compose exec db psql -U app -d app -c "SELECT id, event_type, user_id, email, ip_address, LEFT(user_agent, 50) AS user_agent_prefix, correlation_id, created_at FROM audit_authevent ORDER BY id DESC LIMIT 10;"
```

## Step 10 verification

Manual checks for the reliability and security hardening work completed in step 10:

- With `DJANGO_DEBUG=0`, visit an unknown URL (for example `/missing-page`) and confirm the friendly 404 page appears without a traceback. Trigger an unhandled error (for example by temporarily raising an exception in a view) and confirm the 500 page renders without debug details.
- Attempt to load or modify another user’s vehicle or fill-up by guessing object IDs (such as `/vehicles/1/edit` or `/fillups/1/edit`) and verify the response is `404` when signed in as a different user.
- Open the fill-up creation form and confirm only your vehicles appear in the dropdown, and submissions for other users’ vehicles return a 404.
- Inspect the response headers for `/` and `/vehicles` and confirm `X-Content-Type-Options` and `Referrer-Policy` are always present. When running with `DJANGO_DEBUG=0`, also confirm a `Content-Security-Policy: default-src 'self'` header is applied.
- Check `/health` while `DJANGO_DEBUG=0` to confirm the JSON shape matches debug mode and that any `reason` strings remain short and do not reveal stack traces.
