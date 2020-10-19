import traceback
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


import core.api as API

from flask import request
from flask_api import FlaskAPI, status, exceptions
app = FlaskAPI(__name__)

@app.route('/documents/', methods=['GET'])
def search_102 ():
    return create_request_and_serve(request, API.DocumentsRequest)

@app.route('/combinations/', methods=['GET'])
def seach_103():
    return create_request_and_serve(request, API.SearchRequest103)

@app.route('/snippets/', methods=['GET'])
def get_snippet():
    return create_request_and_serve(request, API.SnippetRequest)

@app.route('/mappings/', methods=['GET'])
def get_mapping():
    return create_request_and_serve(request, API.MappingRequest)

@app.route('/datasets/', methods=['GET'])
def get_sample():
    return create_request_and_serve(request, API.DatasetSampleRequest)

@app.route('/prior-art/', methods=['GET'])
def get_patent_prior_art():
    return create_request_and_serve(request, API.PatentPriorArtRequest)

@app.route('/similar/', methods=['GET'])
def get_similar_patents():
    return create_request_and_serve(request, API.SimilarPatentsRequest)

@app.route('/extension/', methods=['GET'])
def handle_incoming_ext_request():
    return create_request_and_serve(request, API.IncomingExtensionRequest)

def create_request_and_serve(req, reqClass):
    try:
        return success(reqClass(req.args.to_dict()).serve())
    except API.BadRequestError as err:
        traceback.print_exc()
        return bad_request(err.message)
    except API.ServerError as err:
        traceback.print_exc()
        return server_error(err.message)
    except API.NotAllowedError as err:
        traceback.print_exc()
        return not_allowed(err.message)

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

def not_allowed(msg=None):
    msg = msg if msg else 'Request disallowed.'
    http_status = status.HTTP_403_FORBIDDEN
    return msg, http_status

if __name__ == '__main__':
    app.run(debug=False, threaded=False)
