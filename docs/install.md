# Installation guide

## Development

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
    cp ./artdb/artb/env-skel ./artdb/artdb/.env
    vi ./artdb/artdb/.env
    ```

* Install latest python 3.8 and create virtualenv e.g. via `pyenv` and `pyenv-virtualenv`

* Install pip-tools and requirements in your virtualenv:

    ```bash
    pip install pip-tools
    cd artdb
    pip-sync
    cd ..
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
