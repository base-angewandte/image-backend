#!/bin/bash

set -e

if docker compose exec "${PROJECT_NAME}"-django python manage.py showmigrations auth --list | grep -q "\[X\] 0001_initial" && docker compose exec "${PROJECT_NAME}"-django python manage.py showmigrations accounts --list | grep -q "\[ \] 0001_initial"; then
	CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
	git checkout 97cf6749cebef7e84ef98df4875d0f2c265efc39
	docker compose exec "${PROJECT_NAME}"-django uv pip sync requirements.txt
	docker compose exec "${PROJECT_NAME}"-django python manage.py migrate auth
	docker compose exec "${PROJECT_NAME}"-django python manage.py migrate --fake accounts 0001
	git checkout "$CURRENT_BRANCH"
	docker compose exec "${PROJECT_NAME}"-django uv pip sync requirements.txt
	docker compose exec "${PROJECT_NAME}"-django python manage.py migrate
fi
