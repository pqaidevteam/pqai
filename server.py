
import os
import traceback
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from config import config
if config.gpu_disabled:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

from flask import request, send_file
from flask_api import FlaskAPI, status, exceptions

app = FlaskAPI(__name__)
app.url_map.strict_slashes = False

import core.api as API

############################### AUTHENTICATION ###############################

import auth
tokens = auth.read_tokens()

@app.before_request
def validate_token():
    route = request.base_url
    extensions = ('.css', '.js', '.ico')
    if '/drawings' in route:
        pass
    elif '/thumbnails' in route:
        pass
    elif route.endswith(extensions):
        pass
    else:
        token = request.args.to_dict().get('token')
        if not token in tokens:
            return error(API.NotAllowedError('Invalid token.'))


################################ SEARCH ROUTES ################################

@app.route('/search/102/', methods=['GET'])
def search_102():
    return create_request_and_serve(request, API.SearchRequest102)

@app.route('/search/103/', methods=['GET'])
def search_103():
    return create_request_and_serve(request, API.SearchRequest103)

@app.route('/prior-art/patent/', methods=['GET'])
def get_patent_prior_art():
    return create_request_and_serve(request, API.PatentPriorArtRequest)

@app.route('/similar/', methods=['GET'])
def get_similar_patents():
    return create_request_and_serve(request, API.SimilarPatentsRequest)

@app.route('/snippets/', methods=['GET'])
def get_snippet():
    return create_request_and_serve(request, API.SnippetRequest)

@app.route('/mappings/', methods=['GET'])
def get_mapping():
    return create_request_and_serve(request, API.MappingRequest)

@app.route('/datasets/', methods=['GET'])
def get_sample():
    return create_request_and_serve(request, API.DatasetSampleRequest)

@app.route('/extension/', methods=['GET'])
def handle_incoming_ext_request():
    return create_request_and_serve(request, API.IncomingExtensionRequest)


################################# DATA ROUTES #################################

@app.route('/documents/', methods=['GET'])
def get_document():
    return create_request_and_serve(request, API.DocumentRequest)

@app.route('/patents/<pn>', methods=['GET'])
def get_patent_data(pn):
    return create_request_and_serve({'pn': pn}, API.PatentDataRequest)
    
@app.route('/patents/<pn>/title', methods=['GET'])
def get_title(pn):
    return create_request_and_serve({'pn': pn}, API.TitleRequest)
    
@app.route('/patents/<pn>/abstract', methods=['GET'])
def get_abstract(pn):
    return create_request_and_serve({'pn': pn}, API.AbstractRequest)
    
@app.route('/patents/<pn>/claims/', methods=['GET'])
def get_claims(pn):
    return create_request_and_serve({'pn': pn}, API.AllClaimsRequest)
    
@app.route('/patents/<pn>/claims/<n>', methods=['GET'])
def get_one_claim(pn, n):
    return create_request_and_serve({'pn': pn, 'n': int(n)}, API.OneClaimRequest)
    
@app.route('/patents/<pn>/claims/independent', methods=['GET'])
def get_ind_claims(pn):
    return create_request_and_serve({'pn': pn}, API.IndependentClaimsRequest)
    
@app.route('/patents/<pn>/description', methods=['GET'])
def get_description(pn):
    return create_request_and_serve({'pn': pn}, API.PatentDescriptionRequest)
    
@app.route('/patents/<pn>/citations', methods=['GET'])
def get_citations(pn):
    return create_request_and_serve({'pn': pn}, API.CitationsRequest)
    
@app.route('/patents/<pn>/citations/backward', methods=['GET'])
def get_backcits(pn):
    return create_request_and_serve({'pn': pn}, API.BackwardCitationsRequest)
    
@app.route('/patents/<pn>/citations/forward', methods=['GET'])
def get_for_cits(pn):
    return create_request_and_serve({'pn': pn}, API.ForwardCitationsRequest)
    
@app.route('/patents/<pn>/abstract/concepts', methods=['GET'])
def get_abs_concepts(pn):
    return create_request_and_serve({'pn': pn}, API.AbstractConceptsRequest)

@app.route('/patents/<pn>/description/concepts', methods=['GET'])
def get_desc_concepts(pn):
    return create_request_and_serve({'pn': pn}, API.DescriptionConceptsRequest)
    
@app.route('/patents/<pn>/classification/cpcs', methods=['GET'])
def get_cpcs(pn):
    return create_request_and_serve({'pn': pn}, API.CPCsRequest)
    
@app.route('/patents/<pn>/vectors/cpcs', methods=['GET'])
def get_pat_cpc_vec(pn):
    return create_request_and_serve({'pn': pn}, API.PatentCPCVectorRequest)
    
@app.route('/patents/<pn>/vectors/abstract', methods=['GET'])
def get_pat_abs_vec(pn):
    return create_request_and_serve({'pn': pn}, API.PatentAbstractVectorRequest)
    
@app.route('/concepts/<concept>/similar', methods=['GET'])
def get_similar_concepts(concept):
    return create_request_and_serve({'concept': concept}, API.SimilarConceptsRequest)
    
@app.route('/concepts/<concept>/vector', methods=['GET'])
def get_concept_vec(concept):
    return create_request_and_serve({'concept': concept}, API.ConceptVectorRequest)

@app.route('/patents/<pn>/thumbnails', methods=['GET'])
def get_thumbnails_list(pn):
    return create_request_and_serve({'pn': pn}, API.ListThumbnailsRequest)

@app.route('/patents/<pn>/drawings/', methods=['GET'])
def list_patent_drawings(pn):
    return create_request_and_serve({'pn': pn}, API.ListDrawingsRequest)

@app.route('/patents/<pn>/thumbnails/<n>', methods=['GET'])
def get_thumbnail(pn, n):
    return create_request_and_serve_jpg({'pn': pn, 'n': n}, API.ThumbnailRequest)

@app.route('/patents/<pn>/drawings/<n>/', methods=['GET'])
def get_patent_drawing(pn, n):
    return create_request_and_serve_jpg({'pn': pn, 'n': n}, API.DrawingRequest)

############################### ROUTES END HERE ###############################


def create_request_and_serve(req, reqClass):
    try:
        req_data = req if isinstance(req, dict) else req.args.to_dict()
        return success(reqClass(req_data).serve())
    except Exception as e:
        return error(e)

def create_request_and_serve_jpg(req, reqClass):
    try:
        req_data = req if isinstance(req, dict) else req.args.to_dict()
        file_path_local = reqClass(req_data).serve()
        return send_file(file_path_local, mimetype='image/jpeg')
    except Exception as e:
        return error(e)

def success(response):
    return response, status.HTTP_200_OK

def error(e):
    traceback.print_exc()
    if isinstance(e, API.BadRequestError):
        msg = e.message if e.message else 'Bad Request'
        return msg, status.HTTP_400_BAD_REQUEST
    
    elif isinstance(e, API.ServerError):
        msg = e.message if e.message else 'Server error'
        return msg, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    elif isinstance(e, API.NotAllowedError):
        msg = e.message if e.message else 'Request disallowed'
        return msg, status.HTTP_403_FORBIDDEN
    
    elif isinstance(e, API.ResourceNotFoundError):
        msg = e.message if e.message else 'Resource not found'
        return msg, status.HTTP_404_NOT_FOUND


if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=config.port)
