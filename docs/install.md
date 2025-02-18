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

- Install docker with compose plugin for your system

- Clone git repository and checkout branch `develop`:

  ```bash
  git clone https://***REMOVED***/image.git
  cd image
  git checkout develop
  ```

- Check and adapt settings (if you need more details on the single settings, than the comments in the skeleton env
  file give you, take a look at the [](./configuration.md) section) :

  ```bash
  cp env-skel .env
  vi .env
  ```

- Create the docker compose override file:

  ```bash
  cp compose.override.dev.yaml compose.override.yaml
  ```

Now, depending on which path you want to go, take one of the following two
subsections.

### Everything inside docker

- Make sure that the `DOCKER` variable in `.env` is set to
  `TRUE`. Otherwise, django will assume that postgres and redis are accessible
  on localhost ports.
- Also in `.env`, make sure the variable `FORCE_SCRIPT_NAME=` is uncommented and set to an empty string.

- Start everything:

  ```bash
  make start-dev-docker
  ```

  If this is your first start, you will also need to apply the initial
  migrations (can be skipped, unless you reset your database):

  ```bash
  make init
  ```

  To stop all services again hit CTRL-C to stop following the logs and then use `make stop`.

- To additionally get some initial test data into the database:

  ```bash
  make test-data
  ```

  If you also want to include a test data set with artworks containing
  discriminatory terms that should be contextualised (and sometimes, depending
  on context not), you need to do the following (after you loaded the
  test-data with the last command):

  ```bash
  docker compose exec image-django python manage.py loaddata artworks/fixtures/artworks_word_filter_test.json
  ```

### The full developer setup

- Install the latest python 3.11 and create virtualenv e.g. via `pyenv` and `pyenv-virtualenv`.

- Install uv and requirements in your virtualenv:

  ```bash
  pip install uv
  uv pip sync src/requirements-dev.txt
  ```

- Check the _compose.override.dev.yaml_ file you created before from the template
  and uncomment the port mounts for Redis and Postgres, so your local Django can access them.

- Start required services:

  ```bash
  make start-dev
  ```

- Run migrations and install the pre-commit hooks:

  ```bash
  make init-dev
  ```

- Start development server:

  ```bash
  cd src && python manage.py runserver 8300
  ```

- To additionally get some initial test data into the database:

  ```bash
  python manage.py loaddata artworks/fixtures/artists.json
  python manage.py loaddata artworks/fixtures/keywords.json
  python manage.py loaddata artworks/fixtures/locations.json
  python manage.py loaddata artworks/fixtures/discriminatory_terms.json
  python manage.py loaddata artworks/fixtures/artworks.json
  cp ../test-data/image-placeholder-*.png assets/media
  python manage.py load_test_images
  rm assets/media/image-placeholder-*.png
  ```

  If you also want to include a test data set with artworks containing
  discriminatory terms that should be contextualised (and sometimes, depending
  on context not), you need to do the following (after you loaded the
  discriminatory terms):

  ```bash
  python manage.py loaddata artworks/fixtures/artworks_word_filter_test.json
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

- Update package index:

  ```bash
  # RHEL
  sudo yum update

  # Debian
  sudo apt-get update
  ```

- Install docker with compose plugin

- Change to user `base`

- Change to `/opt/base`

- Clone git repository and checkout branch `main` for production or
  `develop` for development:

  ```bash
  git clone https://***REMOVED***/image.git
  cd image
  git checkout <develop|main>
  ```

- Check and adapt settings:

  ```bash
  cp env-skel .env
  vi .env
  ```

- Use `Makefile` to initialize and run project:

  ```bash
  make start init init-static restart-gunicorn
  ```
