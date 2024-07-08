#!/bin/bash

set -e

read -r -p "Are you sure you want to migrate data from the old PostgreSQL 10 database to the new one? [y/N] " answer

case $answer in
[yY]) true ;;
*) exit ;;
esac

PGM_COMPOSE_FILE=docker-compose.postgres.migrate.yml

echo "shutting down all services"
docker compose down

echo "starting up old and new postgres containers"
docker compose -f ${PGM_COMPOSE_FILE} up -d "${PROJECT_NAME}"-postgres "${PROJECT_NAME}"-postgres-old

echo "waiting for postgres containers to start up..."
sleep 3

if ! [[ -z $DB_NAME || -z $DB_USER ]]; then
	# rename old user and database
	echo "old database name and user is set, renaming them in the old database"
	echo "CREATE USER root SUPERUSER;" | docker compose -f ${PGM_COMPOSE_FILE} exec -T "${PROJECT_NAME}"-postgres-old psql postgres -U "${DB_USER}"
	echo "ALTER DATABASE ${DB_NAME} RENAME TO ${POSTGRES_DB}; ALTER USER ${DB_USER} RENAME TO ${POSTGRES_USER};" | docker compose -f ${PGM_COMPOSE_FILE} exec -T "${PROJECT_NAME}"-postgres-old psql postgres -U root
	echo "DROP USER root;" | docker compose -f ${PGM_COMPOSE_FILE} exec -T "${PROJECT_NAME}"-postgres-old psql postgres -U "${POSTGRES_USER}"
fi

echo "migrating data"
docker compose -f ${PGM_COMPOSE_FILE} exec "${PROJECT_NAME}"-postgres-old pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | docker compose exec -T "${PROJECT_NAME}"-postgres psql -U "${POSTGRES_USER}" "${POSTGRES_DB}"

echo "shutting down postgres containers"
docker compose -f ${PGM_COMPOSE_FILE} down

echo "data successfully migrated"
