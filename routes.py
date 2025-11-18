import core.api as API

routes_config = [
    {
        "method": "GET",
        "path": "/search/102/",
        "handler": API.SearchRequest102,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/search/103/",
        "handler": API.SearchRequest103,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/search/102+103/",
        "handler": API.SearchRequestCombined102and103,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/prior-art/patent/",
        "handler": API.PatentPriorArtRequest,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/similar/",
        "handler": API.SimilarPatentsRequest,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/snippets/",
        "handler": API.SnippetRequest,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/mappings/",
        "handler": API.MappingRequest,
        'rateLimit': 5,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/datasets/",
        "handler": API.DatasetSampleRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        "method": "GET",
        "path": "/extension/",
        "handler": API.IncomingExtensionRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/documents/',
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
        'handler': API.TitleRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/abstract',
        'handler': API.AbstractRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/claims/',
        'handler': API.AllClaimsRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/claims/independent',
        'handler': API.IndependentClaimsRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/claims/{n}',
        'handler': API.OneClaimRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/description',
        'handler': API.PatentDescriptionRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/citations',
        'handler': API.CitationsRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/citations/backward',
        'handler': API.BackwardCitationsRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/citations/forward',
        'handler': API.ForwardCitationsRequest,
        'rateLimit': 100,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/citations/aggregated',
        'handler': API.AggregatedCitationsRequest,
        'rateLimit': 10,
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
        'handler': API.CPCsRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/vectors/cpcs',
        'handler': API.PatentCPCVectorRequest,
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
        'handler': API.ListThumbnailsRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/drawings/',
        'handler': API.ListDrawingsRequest,
        'rateLimit': 10,
        'protected': True
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/thumbnails/{n}',
        'handler': API.ThumbnailRequest,
        'is_jpg': True,
        "rateLimit": -1,
        'protected': False
    },
    {
        'method': 'GET',
        'path': '/patents/{pn}/drawings/{n}/',
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
