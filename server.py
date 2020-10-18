# Server
from flask import request
from flask_api import FlaskAPI, status, exceptions
from core.api import BadRequestError, ServerError
from core.api import SearchRequest102, SearchRequest103
from core.api import SnippetRequest, MappingRequest
from core.api import DatasetSampleRequest


import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


app = FlaskAPI(__name__)


@app.route('/documents/', methods=['GET'])
def search_102 ():
    return create_request_and_serve(request, SearchRequest102)

@app.route('/combinations/', methods=['GET'])
def seach_103():
    return create_request_and_serve(request, SearchRequest103)

@app.route('/snippets/', methods=['GET'])
def get_snippet():
    return create_request_and_serve(request, SnippetRequest)

@app.route('/mappings/', methods=['GET'])
def get_mapping():
    return create_request_and_serve(request, MappingRequest)

@app.route('/datasets/', methods=['GET'])
def get_sample():
    return create_request_and_serve(request, DatasetSampleRequest)


def create_request_and_serve(request, RequestClass):
    try:
        request = RequestClass(request.args.to_dict())
        response = request.serve()
        return success(response)
    except BadRequestError as err:
        return bad_request(err.message)
    except ServerError as err:
        return server_error(err.message)

def success(response):
    return response, status.HTTP_200_OK

def server_error(msg=None):
    msg = msg if msg else 'Server error'
    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    return msg, http_status

def bad_request(msg=None):
    msg = msg if msg else 'Bad request'
    http_status = status.HTTP_400_BAD_REQUEST
    return msg, http_status


if __name__ == '__main__':
    app.run(debug=False, threaded=False)
