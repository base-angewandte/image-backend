include .env
export

PROJECT_NAME ?= artdb

include config/base.mk

.PHONY: cleanup
cleanup:  ## clear sessions
	docker-compose exec ${PROJECT_NAME}-django bash -c "python manage.py clearsessions && python manage.py django_cas_ng_clean_sessions"

.PHONY: start-dev
start-dev:  ## start containers for local development
	docker-compose up -d --build \
		artdb-redis \
		artdb-postgres

.PHONY: test-data
test-data:  ## load test/placeholder data (fixtures and image files)
	docker-compose exec artdb-django python manage.py loaddata artworks/fixtures/artists.json
	docker-compose exec artdb-django python manage.py loaddata artworks/fixtures/keywords.json
	docker-compose exec artdb-django python manage.py loaddata artworks/fixtures/locations.json
	docker-compose exec artdb-django python manage.py loaddata artworks/fixtures/artworks.json
	cp test-data/*.png ${MEDIA_DIR}
	docker-compose exec -T artdb-postgres psql -U django_artdb django_artdb < test-data/set-placeholder-images.sql

.PHONY: makemessages-docker
makemessages-docker:
	docker-compose exec ${PROJECT_NAME}-django python manage.py makemessages -l de
	docker-compose exec ${PROJECT_NAME}-django python manage.py makemessages -l en

.PHONY: compilemessages-docker
compilemessages-docker:
	docker-compose exec ${PROJECT_NAME}-django python manage.py compilemessages
