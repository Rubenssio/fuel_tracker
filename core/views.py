"""Views for the bootstrap service."""
from __future__ import annotations

from django.db import connection
from django.db.migrations.exceptions import MigrationSchemaMissing
from django.db.migrations.executor import MigrationExecutor
from django.http import HttpRequest, HttpResponse, JsonResponse

from core.models import BaselineSeed


def success_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse("success", content_type="text/plain")


def health_view(request: HttpRequest) -> JsonResponse:
    db_state = {"connected": False, "migrated": False, "seeded": False}
    reasons: list[str] = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
    except Exception:
        reasons.append("database connection failed")
    else:
        db_state["connected"] = True

        try:
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            is_fully_migrated = len(executor.migration_plan(targets)) == 0
        except MigrationSchemaMissing:
            db_state["migrated"] = False
            reasons.append("migration table missing")
        except Exception:
            db_state["migrated"] = False
            reasons.append("unable to determine migration state")
        else:
            db_state["migrated"] = is_fully_migrated
            if not is_fully_migrated:
                reasons.append("pending migrations")

        if db_state["migrated"]:
            try:
                is_seeded = BaselineSeed.objects.filter(
                    pk=BaselineSeed.SENTINEL_PK
                ).exists()
            except Exception:
                reasons.append("unable to verify baseline seed")
            else:
                db_state["seeded"] = is_seeded
                if not is_seeded:
                    reasons.append("baseline seed missing")

    is_healthy = all(db_state.values())
    status_code = 200 if is_healthy else 503
    status_label = "ok" if is_healthy else "degraded"

    payload: dict[str, object] = {"status": status_label, "db": db_state}

    if reasons:
        deduped_reasons = list(dict.fromkeys(reasons))
        payload["reason"] = "; ".join(deduped_reasons)

    return JsonResponse(payload, status=status_code)
