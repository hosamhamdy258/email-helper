#!/bin/bash

set -e

# Path to the .env file
ENV_FILE="./core/.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
	echo ".env file not found in /core Creating one with a generated SECRET_KEY."

	# Generate a SECRET_KEY using Python and write it to the .env file
	SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

	# Create the .env file and add the SECRET_KEY
	echo "DJANGO_SECRET_KEY=$SECRET_KEY" >"$ENV_FILE"
	echo "DJANGO_DEVELOPMENT=False" >>"$ENV_FILE"

fi

# ===========================================
# Migrations Files Generation in Production
# ===========================================

MARKER_FILE="/run/.migrations_done"
APPS_FILE="apps.txt"

if [ -f "$APPS_FILE" ] && [ ! -f "$MARKER_FILE" ]; then
	echo "Running migrations as marker not found and apps list present."
	mapfile -t APPS < <(grep -vE '^\s*(#|$)' "$APPS_FILE")

	if [ ${#APPS[@]} -eq 0 ]; then
		echo "No apps found in $APPS_FILE; skipping makemigrations."
	else
		printf 'Making migrations for apps: %s\n' "${APPS[*]}"
		python manage.py makemigrations "${APPS[@]}"
	fi

	python manage.py migrate
	mkdir -p "$(dirname "$MARKER_FILE")"
	touch "$MARKER_FILE"
	echo "Migrations complete; marker file created at $MARKER_FILE."
	python fill_database.py
fi


# Execute the main command (passed as CMD in Dockerfile)
exec "$@"
