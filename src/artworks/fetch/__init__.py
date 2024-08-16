import requests

from django.conf import settings

from .exceptions import DataNotFoundError, HTTPError, RequestError


def fetch_data(url, headers=None, params=None):
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=settings.REQUESTS_TIMEOUT,
        )
    except requests.RequestException as e:
        raise RequestError from e
    if response.status_code != 200:
        if response.status_code == 404:
            raise DataNotFoundError
        raise HTTPError(
            response.status_code,
            response.text,
        )

    return response.json()


def fetch_getty_data(getty_id):
    if getty_id:
        url = getty_id + '.json'
        return fetch_data(url)


def fetch_gnd_data(gnd_id):
    if gnd_id:
        url = settings.GND_API_BASE_URL + gnd_id
        headers = {'Accept': 'application/json'}
        return fetch_data(url, headers=headers)


def fetch_wikidata(link):
    if link:
        url = link + '.json'
        return fetch_data(url)
