#!/bin/sh
set -e

TARGET="$1"

if [ "$TARGET" = "api" ]; then
    python -m app.cli.legacy_guard || exit 1
    if ! python -m app.cli.pre_migration_dump; then
        echo "Pre-migration backup failed, migrations not applied! Exiting container..."
        exit 1
    fi
    echo "Running database migrations"
    if ! alembic -c alembic.ini upgrade head; then
        echo "Database migration failed! Exiting container..."
        exit 1
    fi
    echo "Migrations applied"
fi

case "$TARGET" in
    api)
        UVICORN_RELOAD_ARGS=""
        if [ "$UVICORN_RELOAD_ENABLED" = "true" ]; then
            echo "Uvicorn will run with reload enabled"
            UVICORN_RELOAD_ARGS="--reload --reload-dir /opt/remnashop/app"
        else
            echo "Uvicorn will run without reload"
            # --reload runs a single process, so APP_WORKERS applies without it only
            UVICORN_RELOAD_ARGS="--workers ${APP_WORKERS:-1}"
        fi
        exec uvicorn app.api.__main__:create_app --factory --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-5000}" --use-colors $UVICORN_RELOAD_ARGS
        ;;
    telegram)
        exec python -m app.telegram
        ;;
    worker)
        # every app/modules/*/tasks.py is imported; the pattern is quoted so
        # taskiq globs it from WORKDIR, not the shell
        # With metrics on, only the first worker process serves the metrics port
        # and polls the queue gauges (app/worker/lifespan.py); the task counters
        # of the other processes aren't exported.
        exec taskiq worker -w "${WORKER_PROCESSES:-1}" --max-async-tasks "${WORKER_MAX_ASYNC_TASKS:-25}" app.core.broker:broker app.worker.lifespan --fs-discover --tasks-pattern "app/modules/*/tasks.py"
        ;;
    scheduler)
        # imports the same tasks modules as the worker to read their schedule
        # labels; it never executes a task.
        # It also dispatches every delayed task retry via retry_schedule_source,
        # so it's an operational dependency for retry timing: a scheduler outage
        # stalls (does not lose -- ListRedisScheduleSource recovers past
        # buckets) all pending retries.
        exec taskiq scheduler app.worker.scheduler:scheduler --fs-discover --tasks-pattern "app/modules/*/tasks.py"
        ;;
    cli)
        exec python -m app.cli
        ;;
    *)
        echo "Usage: docker-entrypoint.sh {api|telegram|worker|scheduler|cli}" >&2
        exit 1
        ;;
esac
