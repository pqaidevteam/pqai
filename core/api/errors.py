class BadRequestError(Exception):

    def __init__(self, msg='Invalid request.'):
        self.message = msg


class ServerError(Exception):

    def __init__(self, msg='Server error while handling request.'):
        self.message = msg


class NotAllowedError(Exception):

    def __init__(self, msg="Request disallowed."):
        self.message = msg


class ResourceNotFoundError(Exception):

    def __init__(self, msg="Resource not found."):
        self.message = msg
