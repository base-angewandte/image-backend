# Configuration

The _Image_ backend is configured through one `.env` file in the project root folder.
There is a template `env-skel` file available in the same folder, to copy from and
then modify it. See also [](install.md) on when and how to set up those file.

## `.env`

The first part of the file is used to configure the docker services, for database
credentials and the static assets folder. The defaults are fine, only the
`POSTGRES_PASSWORD` should be set to a strong password.

> Note: we wrote _should_, because programmatically nothing keeps you from using the
> default _password_. But in terms of nearly any security policy you absolutely _MUST_
> set a strong password here. Try e.g. `pwgen -s 32 1`.

If you want to explicitly use a different port for the docker services, you can
configure the `POSTGRES_PORT` and `REDIS_PORT` settings accordingly, but you will also
need to create a `docker-compose.override.yml` file to configure these ports for docker.
See `docker-compose.overridy.dev.yml` for an example of how to do this.

For a production setup you might want to store the uploaded image files not directly
in the default assets folder within Django root. In that case, you can adapt the
`MEDIA_DIR=` and point to your media directory that gets mounted into the Django
container to Django's default assets directory.

The rest of the file contains additional Django configuration. All available settings
are commented, but some are more self-explanatory than others. Some only really make
sense, once you grasp the whole architectural ecosystem. So here you find some notes
to shed more light on those settings that might seem more opaque, or that are absolutely
needed to run.

### DOCKER

For any online deployment the default (True) should be fine here, as usually all
services will be run inside docker containers. Only when you want to start the
Django application itself on your host machine (e.g. for local development), you have
to set this to False.

### SITE_URL & FORCE_SCRIPT_NAME

The `SITE_URL` has to be set to the base URL of the site _Image_ is running on, which
will depend on whether you deploy this to some online node, either with multiple services
sharing one domain or running _Image_ on a separate domain, or if you run it locally.
For local development setups you can choose `http://127.0.0.1:8300/`. For an online
deployment choose the base path (protocol and domain), e.g. `https://base.uni-ak.ac.at/`.

Additionally, `FORCE_SCRIPT_NAME` (which defaults to `/image`) will be used to
determine the actual PATH to your _Image_ instance, by prefixing it with the
`SITE_URL`. So for a local development setup (where Django is actually running on
127.0.0.1:8300) make sure to remove the comment and explicitly set this to an empty
string:

```
FORCE_SCRIPT_NAME=
```

Do the same if _Image_ runs on the root of a dedicated domain, and leave the
default if it runs on a shared domain where it runs on the _/image_ path.

### BEHIND_PROXY

This defines whether your application is running behind a reverse proxy (e.g. nginx).
In most cases the default True will be fine here. But for local development you might
want to set this to False.

### EMAIL\_\*

All settings in the block prefixed with `EMAIL_` are needed if you want to receive
e-Mail notifications from Django. While this is usually not necessary for local
development environments, it is highly advised for staging and production deployments.

### CORS\_\* & CSRF\_\*

All settings should basically be fine by default, as long as your frontend runs on the
same domain as the backend. If you need frontends on different domains (e.g. for
testing and staging purposes) to be able to make those request, you should add them
to the `CSRF_TRUSTED_ORIGINS` and `CORS_ALLOWED_ORIGINS` lists. You should also set
`CORS_ALLOW_CREDENTIALS` to `True` to be able to make authenticated requests on behalf
of the user. Downloads in the frontend only work if you also add `content-disposition`
to `CORS_EXPOSE_HEADERS`.

### CAS_SERVER

The `CAS_SERVER` points to the base path of your authentication server (e.g.
https://base.uni-ak.ac.at/cas/).

### BASE_HEADER_SITE_URL

The base header is the old header row with links to other base applications next
to image. This will be deprecated soon, as for image 2.0 we are developing a
separate frontend that will be responsible for loading the base header. Until
then, if you want to have the base header included in image's root page, set
this some site with available base header, e.g. https://***REMOVED***/
