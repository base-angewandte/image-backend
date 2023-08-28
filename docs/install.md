# Installation guide

## Development

There are two supported ways to start the development server:

1. Start only the auxiliary servers (database and redis) in docker
   but start the django dev server locally in your virtual env. This
   is the preferred way if you actively develop this application.

2. Start everything inside docker containers. This is the "easy" way
   to start a dev server and fiddle around with it, hot reloading included.
   But you will not have the local pre-commit setup.

In both cases there are some common steps to follow:

* Install docker and docker-compose for your system

* Clone git repository and checkout branch `develop`:

    ```bash
    git clone https://***REMOVED***/image.git
    cd image
    git checkout develop
    ```

* Check and adapt settings:

    ```bash
    # env
    cp env-skel .env
    vi .env
    
    # django env
    cp ./artdb/artdb/env-skel ./artdb/artdb/.env
    vi ./artdb/artdb/.env
    ```
Take a look at the [](./configuration.md) section, for more details, if you need more
context than the comments in the skeleton env files give you.

Now, depending on which path you want to go, take one of the following two
subsections.

### Everything inside docker 

* Make sure that the `DOCKER` variable in `./artdb/artdb/.env` is set to
  `TRUE`. Otherwise, django will assume that postgres and redis are accessible
  on localhost ports.

* Start everything:
    ```bash
    make start-dev-docker
    ```
  If this is your first start, you will also need to apply the initial
  migrations (can be skipped, unless you reset your database):
    ```bash
    make init
    ```
  To stop all services again hit CTRL-C to stop following the logs  and then use `make stop`.

* To additionally get some initial test data into the database:
    ```bash
    make test-data
    ```

### The full developer setup

> Disclaimer: make sure to explicitly set the relevant `POSTGRES_*` variables in your
> artdb/artdb/.env file, if you have changed any of the corresponding `DB_*`
> parameters in your .env file. This is not necessary for dockerised setups, but in your
> local django dev server those environement variables are not assigned
> automagically. Take a look at the [](./configuration.md) section for details.

* Install the latest python 3.8 and create virtualenv e.g. via `pyenv` and `pyenv-virtualenv`.

* Install pip-tools and requirements in your virtualenv:

    ```bash
    pip install pip-tools
    cd artdb
    pip-sync
    cd ..
    ```

* Create the docker-compose override file:

    ```bash
    cp docker-compose.override.dev.yml docker-compose.override.yml
    ```

* Start required services:

    ```bash
    make start-dev
    ```
    
* Run migration:

    ```bash
    cd artdb
    python manage.py migrate
    ```

* Start development server:

    ```bash
    python manage.py runserver 8300
    ```

* To additionally get some initial test data into the database:

    ```bash
	python manage.py loaddata artworks/fixtures/artists.json
	python manage.py loaddata artworks/fixtures/keywords.json
	python manage.py loaddata artworks/fixtures/locations.json
	python manage.py loaddata artworks/fixtures/artworks.json
    cd ..
	cp test-data/*.png artdb/assets/media
	docker-compose exec -T artdb-postgres psql -U django_artdb django_artdb < test-data/set-placeholder-images.sql
    ```

### Resetting your database and/or the cache

In both cases you sometimes might want to start with a fresh database, or need
to clear the whole cache. If you need to do so, make sure to stop the containers
first (`make stop`). Then delete the _./dockerdata/postgres_ folder (for the database)
and/or the _./dockerdata/redis_ folder (for the cache). Once you start the containers
again as described above, you have a new database and/or a fresh cache. If you cleared
the database you have to apply the migrations again, so start again from the `make init`
or `python manage.py migrate` steps above


## Production

* Update package index:

    ```bash
    # RHEL
    sudo yum update

    # Debian
    sudo apt-get update
    ```

* Install docker and docker-compose 
(see [base documentation](https://***REMOVED***/documentation/base/server.html#docker))

* Change to user `base`

* Change to `/opt/base`

* Clone git repository and checkout branch `master` for production or 
`develop` for development:

    ```bash
    git clone https://***REMOVED***/image.git
    cd image
    git checkout <develop|master>
    ```

* Check and adapt settings:

    ```bash
    # env
    cp env-skel .env
    vi .env
    
    # django env
    cp ./artdb/artdb/env-skel ./artdb/artdb/.env
    vi ./artdb/artdb/.env
    ```

* Use `Makefile` to initialize and run project:

    ```bash
    make start init init-static restart-gunicorn
    ```
