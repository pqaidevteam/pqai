import core.api as API

routes_config = [
    {
        "method": "GET",
        "path": "/search/102",
        "handler": API.SearchRequest102,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/search/103",
        "handler": API.SearchRequest103,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/search/102+103",
        "handler": API.SearchRequestCombined102and103,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/prior-art/patent",
        "handler": API.PatentPriorArtRequest,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/similar",
        "handler": API.SimilarPatentsRequest,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/snippets",
        "handler": API.SnippetRequest,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/mappings",
        "handler": API.MappingRequest,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/extension",
        "handler": API.IncomingExtensionRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/documents',
        'handler': API.DocumentRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}',
        'handler': API.PatentDataRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/title',
        'handler': lambda d: API.PatentDataRequest({**d, 'fields': 'title'}),
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/abstract',
        'handler': lambda d: API.PatentDataRequest({**d, 'fields': 'abstract'}),
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/claims',
        'handler': lambda d: API.PatentDataRequest({**d, 'fields': 'claims'}),
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/claims/independent',
        'handler': lambda d: API.PatentDataRequest({**d, 'fields': 'independent_claims'}),
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/description',
        'handler': lambda d: API.PatentDataRequest({**d, 'fields': 'description'}),
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/citations',
        'handler': lambda d: API.PatentDataRequest({**d, 'fields': 'citations_backward,citations_forward'}),
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/citations/backward',
        'handler': lambda d: API.PatentDataRequest({**d, 'fields': 'citations_backward'}),
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/citations/forward',
        'handler': lambda d: API.PatentDataRequest({**d, 'fields': 'citations_forward'}),
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/abstract/concepts',
        'handler': API.AbstractConceptsRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/description/concepts',
        'handler': API.DescriptionConceptsRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/classification/cpcs',
        'handler': lambda d: API.PatentDataRequest({**d, 'fields': 'cpcs'}),
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/vectors/abstract',
        'handler': API.PatentAbstractVectorRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/thumbnails',
        'handler': API.ListDrawingsRequest, # using same handler as drawings
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/drawings',
        'handler': API.ListDrawingsRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/thumbnails/{n}',
        'handler': lambda d: API.DrawingRequest({'h': 200, **d}),
        'is_jpg': True,
        "rateLimit": -1,
        'protected': False
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/drawings/{n}',
        'handler': API.DrawingRequest,
        'is_jpg': True,
        "rateLimit": -1,
        'protected': False
    },
    {
        'method': 'GET',
        'path': '/concepts/{concept}/similar',
        'handler': API.SimilarConceptsRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/concepts/{concept}/vector',
        'handler': API.ConceptVectorRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/docs',
        'handler': API.DocumentationRequest,
        'rateLimit': -1,
        'protected': False
    }
]
