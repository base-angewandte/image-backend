class BaseApiDataError(Exception):
    pass


class DataNotFoundError(BaseApiDataError):
    pass


class RequestError(BaseApiDataError):
    pass


class HTTPError(BaseApiDataError):
    def __init__(self, status_code, details=None):
        self.status_code = status_code
        self.details = details
