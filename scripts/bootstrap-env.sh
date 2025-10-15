#!/usr/bin/env sh
set -eu
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Review and adjust values if needed."
else
  echo ".env already exists; not modifying."
fi
