include .env
export


start:
	docker-compose up -d --build

stop:
	docker-compose down

restart:
	docker-compose restart

git-update:
	if [ "$(shell whoami)" != "base" ]; then sudo -u base git pull; else git pull; fi

init:
	docker-compose exec artdb-django bash -c "pip-sync && python manage.py migrate"

init-static:
	docker-compose exec artdb-django bash -c "python manage.py collectstatic --noinput"

cleanup:
	docker-compose exec artdb-django bash -c "python manage.py clearsessions && python manage.py django_cas_ng_clean_sessions"

build-image:
	docker-compose build artdb-django

restart-gunicorn:
	docker-compose exec artdb-django bash -c 'kill -HUP `cat /var/run/django.pid`'

build-docs:
	docker build -t image-docs ./docker/docs
	docker run -it -v `pwd`/docs:/docs -v `pwd`/artdb:/src image-docs make clean html

update: git-update init init-static restart-gunicorn

start-dev:
	docker-compose up -d --build \
		artdb-redis \
		artdb-postgres

.PHONY: start-dev-docker
start-dev-docker: start  ## start docker development setup
	docker logs -f artdb-django

.PHONY: test-data
test-data:
	docker-compose exec artdb-django python manage.py loaddata artworks/fixtures/artists.json
	docker-compose exec artdb-django python manage.py loaddata artworks/fixtures/keywords.json
	docker-compose exec artdb-django python manage.py loaddata artworks/fixtures/locations.json
	docker-compose exec artdb-django python manage.py loaddata artworks/fixtures/artworks.json
	cp test-data/*.png ${MEDIA_DIR}
	docker-compose exec -T artdb-postgres psql -U django_artdb django_artdb < test-data/set-placeholder-images.sql
