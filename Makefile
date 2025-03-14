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
		${PROJECT_NAME}-postgres \
		${PROJECT_NAME}-gotenberg

.PHONY: update
update: git-update init-rq init restart-gunicorn collectstatic build-docs  ## update project (runs git-update init-rq init restart-gunicorn collectstatic build-docs)


.PHONY: test-data
test-data:  ## load test/placeholder data (fixtures and image files)
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/artists.json
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/keywords.json
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/locations.json
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/discriminatory_terms.json
	docker compose exec ${PROJECT_NAME}-django python manage.py loaddata artworks/fixtures/artworks.json
	cp test-data/image-placeholder-*.png ${MEDIA_DIR}
	docker compose exec ${PROJECT_NAME}-django python manage.py load_test_images
	rm ${MEDIA_DIR}/image-placeholder-*.png

.PHONY: run-api-tests
run-api-tests:  ## run all available api tests
	docker compose exec ${PROJECT_NAME}-django python manage.py test api.tests

.PHONE: coverage-api-tests
coverage-api-tests:  ## compute coverage of api tests
	docker compose exec ${PROJECT_NAME}-django coverage run --source='.' manage.py test api.tests
	docker compose exec ${PROJECT_NAME}-django coverage report -m --skip-empty

.PHONE: coverage-api-tests-html
coverage-api-tests-html:  ## compute coverage of api tests and create html output
	docker compose exec ${PROJECT_NAME}-django coverage run --source='.' manage.py test api.tests
	docker compose exec ${PROJECT_NAME}-django coverage html --skip-empty

.PHONY: migrate-postgres
migrate-postgres:  ## migrate data from old PostgreSQL database to new one
	@bash scripts/migrate-postgres.sh

.PHONY: migrate-user-model
migrate-user-model:  ## migrate user model from django.contrib.auth to accounts
	@bash scripts/migrate-user-model.sh

.PHONY: init-rq
init-rq:  ## init rq worker
	docker compose exec ${PROJECT_NAME}-rq-worker bash -c "uv pip sync requirements.txt"

.PHONY: init
init:  ## init django project
	docker compose exec ${PROJECT_NAME}-django bash -c "uv pip sync requirements.txt && python manage.py migrate"
ifeq ($(DEBUG),True)
	@make pre-commit-init
endif

.PHONY: collectstatic
collectstatic:
	docker compose exec ${PROJECT_NAME}-django python manage.py collectstatic --noinput
