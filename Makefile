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
