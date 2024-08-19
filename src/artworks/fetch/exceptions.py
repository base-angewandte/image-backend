class FetchDataError(Exception):
    pass


class DataNotFoundError(FetchDataError):
    pass


class RequestError(FetchDataError):
    pass


class HTTPError(FetchDataError):
    def __init__(self, status_code, details=None):
        self.status_code = status_code
        self.details = details
