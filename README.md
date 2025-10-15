# Fuel Tracker Bootstrap Service

This repository contains a minimal Django application that responds with a success page and a JSON health check. The service is packaged for local development using Docker Compose.

## Running locally

1. Build and start the container:
   ```bash
   docker compose up --build
   ```
2. Open the service in your browser:
   - http://localhost:8000/ should display `success`.
   - http://localhost:8000/health should return `{ "status": "ok" }`.

Use `Ctrl+C` to stop the server when you're done.
