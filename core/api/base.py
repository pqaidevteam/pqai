import traceback
from pydantic import ValidationError

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

class APIRequest():
    _schema = None

    def __init__(self, req_data=None):
        if self._schema:
            try:
                validated = self._schema(**req_data)
                self._params = validated.model_dump()
                for key in self._params:
                    if not hasattr(self, key):
                        setattr(self, key, self._params[key])

            except ValidationError as e:
                raise BadRequestError(str(e))
        else:
            self._params = req_data or {}

    def serve(self):
        try:
            response = self._serve()
            return self._format(response)
        except BadRequestError as e:
            raise e
        except ResourceNotFoundError as e:
            raise e
        except Exception:
            traceback.print_exc()
            raise ServerError()

    def _serve(self):
        raise NotImplementedError()

    def _format(self, response):
        return response