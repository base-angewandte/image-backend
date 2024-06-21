include .env
export

PROJECT_NAME ?= image

include config/base.mk

.PHONY: cleanup
cleanup:  ## clear sessions
	docker compose exec ${PROJECT_NAME}-django bash -c "python manage.py clearsessions && python manage.py django_cas_ng_clean_sessions"

.PHONY: start-dev
start-dev:  ## start containers for local development
	docker compose up -d --build \
		${PROJECT_NAME}-redis \
		${PROJECT_NAME}-postgres

.PHONY: test-data
test-data:  ## load test/placeholder data (fixtures and image files)
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/artists.json
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/keywords.json
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/locations.json
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/discriminatory_terms.json
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/artworks.json
	cp test-data/*.png ${MEDIA_DIR}
	docker compose exec -T ${PROJECT_NAME}-postgres psql -U django_${PROJECT_NAME} django_${PROJECT_NAME} < test-data/set-placeholder-images.sql

.PHONY: run-api-tests
run-api-tests:  ## run all available api tests
	docker compose exec ${PROJECT_NAME}-django python manage.py test api.tests

.PHONY: migrate-postgres
migrate-postgres:  ## migrate data from old PostgreSQL database to new one
	@printf "Are you sure you want to migrate data from the old PostgreSQL 10 database to the new one? [y/N] " && read answer && case "$$answer" in [yY]) true;; *) false;; esac
	docker compose down
	docker compose -f docker-compose.postgres.migrate.yml up -d ${PROJECT_NAME}-postgres ${PROJECT_NAME}-postgres-old
	# wait for postgres containers to start up
	sleep 3
ifneq ($(and $(DB_NAME),$(DB_USER)),)
	# rename old user and database
	echo "CREATE USER root SUPERUSER;" | docker compose -f docker-compose.postgres.migrate.yml exec -T ${PROJECT_NAME}-postgres-old psql postgres -U ${DB_USER}
	echo "ALTER DATABASE ${DB_NAME} RENAME TO ${POSTGRES_DB}; ALTER USER ${DB_USER} RENAME TO ${POSTGRES_USER};" | docker compose -f docker-compose.postgres.migrate.yml exec -T ${PROJECT_NAME}-postgres-old psql postgres -U root
	echo "DROP USER root;" | docker compose -f docker-compose.postgres.migrate.yml exec -T ${PROJECT_NAME}-postgres-old psql postgres -U ${POSTGRES_USER}
endif
	# migrate data
	docker compose -f docker-compose.postgres.migrate.yml exec ${PROJECT_NAME}-postgres-old pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} | docker compose exec -T ${PROJECT_NAME}-postgres psql -U ${POSTGRES_USER} ${POSTGRES_DB}
	docker compose -f docker-compose.postgres.migrate.yml down
