import unittest
import sys
from pathlib import Path
from dotenv import load_dotenv
from dateutil.parser import parse as parse_date

# Run tests without using GPU
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ['TEST'] = "1"

TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
ENV_PATH = "{}/.env".format(BASE_DIR)

load_dotenv(ENV_PATH)
sys.path.append(BASE_DIR)

from core.api import (  # noqa: E402
    APIRequest,
    SearchRequest102,
    SearchRequest103,
    SnippetRequest,
    MappingRequest,
    DatasetSampleRequest,
    SimilarPatentsRequest,
    PatentPriorArtRequest
)

from core.api import (  # noqa: E402
    BadRequestError,
    ServerError,
    ResourceNotFoundError
)

from core.api import (  # noqa: E402
    DocumentRequest,
    PatentDataRequest,
    TitleRequest,
    AbstractRequest,
    AllClaimsRequest,
    OneClaimRequest,
    IndependentClaimsRequest,
    PatentDescriptionRequest,
    CitationsRequest,
    BackwardCitationsRequest,
    ForwardCitationsRequest,
    AbstractConceptsRequest,
    CPCsRequest,
    ListThumbnailsRequest,
    ThumbnailRequest,
    PatentCPCVectorRequest,
    PatentAbstractVectorRequest,
    SimilarConceptsRequest,
    ConceptVectorRequest,
    DrawingRequest,
    ListDrawingsRequest,
    AggregatedCitationsRequest
)


class TestRequestClass(unittest.TestCase):

    class GreetingRequest(APIRequest):

        greetings = { 'en': 'Hello', 'de': 'Hallo' }

        def __init__(self, req_data):
            super().__init__(req_data)

        def _serving_fn(self):
            lang = self._data['lang']
            return self.greetings[lang]

        def _validation_fn(self):
            if 'lang' not in self._data:
                raise BadRequestError('Invalid request.')

    def test_can_create_dummy_request(self):
        req = APIRequest()
        self.assertEqual(req.serve(), None)

    def test_serving_fn_operation(self):
        req = self.GreetingRequest({ 'lang': 'en' })
        self.assertEqual('Hello', req.serve())

    def test_raises_error_on_invalid_request(self):
        def create_invalid_request():
            return self.GreetingRequest({ 'locale': 'en' })
        self.assertRaises(BadRequestError, create_invalid_request)

    def test_raises_error_on_expection_during_serving(self):
        req = self.GreetingRequest({ 'lang': 'hi' })
        self.assertRaises(ServerError, req.serve)


class TestSearchRequest102Class(unittest.TestCase):

    def setUp(self):
        self.query = 'reducing carbon emissions'
        self.date = '2017-12-12'
        self.subclass = 'Y02T'
        self.latent_query = 'by using green technologies'

    def test_simple_search_request(self):
        results = self.search({ 'q': self.query })
        self.assertGreater(len(results), 0)

    def test_return_custom_number_of_results(self):
        results = self.search({ 'q': self.query, 'n': 13 })
        self.assertEqual(13, len(results))

    def test_query_with_before_cutoff_date(self):
        results = self.search({ 'q': self.query, 'before': self.date })
        def published_before(r):
            d1 = parse_date(r['publication_date'])
            d2 = parse_date(self.date)
            return d1 <= d2
        self.assertForEach(results, published_before)

    def test_query_with_after_cutoff_date(self):
        results = self.search({ 'q': self.query, 'after': self.date})
        def published_after(r):
            d1 = parse_date(r['publication_date'])
            d2 = parse_date(self.date)
            return d1 >= d2
        self.assertForEach(results, published_after)

    def test_query_with_index_specified(self):
        cc = self.subclass
        results = self.search({ 'q': self.query, 'idx': cc })
        from_cc = lambda r: r['index'].startswith(cc)
        self.assertForEach(results, from_cc)

    def test_latent_query_affects_results(self):
        latent = self.search({ 'q': self.query, 'lq': self.latent_query })
        without = self.search({ 'q': self.query })
        self.assertNotEqual(latent, without)

    def test_return_only_non_patent_results(self):
        results = self.search({ 'q': 'control systems', 'type': 'npl' })
        is_npl = lambda r: r['index'].endswith('npl')
        self.assertForEach(results, is_npl)

    def test_include_snippets(self):
        results = self.search({ 'q': self.query, 'snip': 1 })
        has_snippet = lambda r: r['snippet']
        self.assertForEach(results, has_snippet)

    def test_include_mappings(self):
        results = self.search({ 'q': self.query, 'maps': 1 })
        has_mappings = lambda r: r['mapping']
        self.assertForEach(results, has_mappings)

    def test_raises_error_with_bad_request(self):
        with self.assertRaises(BadRequestError):
            SearchRequest102({ 'qry': self.query })

    def test_pagination(self):
        results_a = self.search({ 'q': self.query, 'n': 10 })
        results_b = self.search({ 'q': self.query, 'n': 10, 'offset': 5})
        self.assertEqual(results_a[5:], results_b[:5])

    def search(self, req):
        req = SearchRequest102(req)
        results = req.serve()['results']
        return results

    def assertForEach(self, results, condition):
        self.assertGreater(len(results), 0)
        truth_arr = [condition(res) for res in results]
        self.assertTrue(all(truth_arr))
        

class TestSearchRequest103Class(unittest.TestCase):

    def setUp(self):
        self.query = 'fire fighting drone uses dry ice'

    def test_simple_search(self):
        combinations = self.search({ 'q': self.query })
        self.assertGreater(len(combinations), 0)

    def test_return_custom_number_of_results(self):
        combinations = self.search({ 'q': self.query, 'n': 8 })
        self.assertEqual(8, len(combinations))

    def test_pagination(self):
        results_a = self.search({ 'q': self.query, 'n': 10 })
        results_b = self.search({ 'q': self.query, 'n': 10, 'offset': 5})
        self.assertEqual(results_a[5:], results_b[:5])

    def search(self, req):
        req = SearchRequest103(req)
        results = req.serve()['results']
        return results


class TestDatasetSampleRequestClass(unittest.TestCase):

    def test_request_a_sample_from_poc(self):
        self.assertSample('poc', 23)
        self.assertSample('poc', 45023)

    def test_request_a_sample_that_does_not_exist(self):
        with self.assertRaises(ServerError):
            self.make_request('poc', 200200)

    def test_access_non_existent_dataset(self):
        with self.assertRaises(ResourceNotFoundError):
            self.make_request('dog', 1)

    def test_invalid_request(self):
        with self.assertRaises(BadRequestError):
            DatasetSampleRequest({ 'sample': 3 }).serve()

    def assertSample(self, dataset, n):
        sample = self.make_request(dataset, n)
        self.assertIsInstance(sample, dict)

    def make_request(self, dataset, n):
        request = DatasetSampleRequest({ 'dataset': dataset, 'n': n })
        return request.serve()


class TestSimilarPatentsRequestClass(unittest.TestCase):

    def test_invalid_query(self):
        with self.assertRaises(BadRequestError):
            SimilarPatentsRequest({ 'q': 'drones'})

    def test_with_simple_query(self):
        response = SimilarPatentsRequest({ 'pn': 'US7654321B2' }).serve()
        self.assertIsInstance(response, dict)
        self.assertIsInstance(response['results'], list)
        self.assertGreater(len(response['results']), 0)


class TestPatentPriorArtRequestClass(unittest.TestCase):

    def test_with_simple_query(self):
        response = PatentPriorArtRequest({ 'pn': 'US7654321B2'}).serve()
        results = response['results']
        def published_before(r):
            d1 = parse_date(r['publication_date'])
            d2 = parse_date('2006-12-27')
            return d1 <= d2
        self.assertForEach(results, published_before)

    def assertForEach(self, results, condition):
        truth_arr = [condition(res) for res in results]
        self.assertTrue(all(truth_arr))


class TestSnippetRequestClass(unittest.TestCase):
    pass


class TestMappingRequestClass(unittest.TestCase):
    pass


class TestDrawingRequestClass(unittest.TestCase):

    def setUp(self):
        self.pat = 'US7654321B2'
        self.app = 'US20130291398A1'

    def test_get_patent_drawing(self):
        response = DrawingRequest({'pn': self.pat, 'n': 1}).serve()
        self.assertIsInstance(response, str)

    def test_get_second_image(self):
        response = DrawingRequest({'pn': self.pat, 'n': 2}).serve()
        self.assertIsInstance(response, str)

    def test_get_publication_drawing(self):
        response = DrawingRequest({'pn': self.app, 'n': 1}).serve()
        self.assertIsInstance(response, str)


class TestListDrawingsRequestClass(unittest.TestCase):

    def setUp(self):
        self.pat = 'US7654321B2'
        self.app = 'US20130291398A1'

    def test_list_drawings_of_patent(self):
        response = ListDrawingsRequest({'pn': self.pat}).serve()
        self.assertEqual(8, len(response['drawings']))
        self.assertEqual(self.pat, response['pn'])

    def test_list_drawings_of_application(self):
        response = ListDrawingsRequest({'pn': self.app}).serve()
        self.assertEqual(12, len(response['drawings']))
        self.assertEqual(self.app, response['pn'])


class TestDocumentRequestClass(unittest.TestCase):

    def test_get_patent_document(self):
        doc = DocumentRequest({'id': 'US7654321B2'}).serve()
        self.assertIsInstance(doc, dict)
        self.assertEqual(doc['id'], 'US7654321B2')


class TestPatentDataRequestClass(unittest.TestCase):

    def test_returns_patent_data(self):
        data = PatentDataRequest({'pn': 'US7654321B2'}).serve()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['title'][:24], 'Formation fluid sampling')
        self.assertEqual(data['pn'], 'US7654321B2')
        self.assertNonNullString(data['abstract'])
        self.assertNonNullString(data['description'])
        self.assertIsInstance(data['claims'], list)
        self.assertGreater(len(data['claims']), 0)

    def assertNonNullString(self, string):
        self.assertIsInstance(string, str)
        self.assertGreater(len(string.strip()), 0)


class TestTitleRequestClass(unittest.TestCase):
    
    def test_get_title(self):
        pn = 'US7654321B2'
        title = 'Formation fluid sampling apparatus and methods'
        response = TitleRequest({'pn': pn}).serve()
        self.assertEqual(response['pn'], pn)
        self.assertEqual(response['title'], title)


class TestAbstractRequestClass(unittest.TestCase):
    
    def test_get_abstract(self):
        pn = 'US7654321B2'
        abst = 'A fluid sampling system retrieves'
        response = AbstractRequest({'pn': pn}).serve()
        self.assertEqual(response['pn'], pn)
        self.assertEqual(response['abstract'][:len(abst)], abst)


class TestAllClaimsRequestClass(unittest.TestCase):
   
    def test_get_all_claims(self):
        pn = 'US7654321B2'
        response = AllClaimsRequest({'pn': pn}).serve()
        self.assertIsInstance(response['claims'], list)
        self.assertEqual(26, len(response['claims']))


class TestOneClaimRequestClass(unittest.TestCase):

    def setUp(self):
        self.pn = 'US7654321B2'
    
    def test_get_one_claim(self):
        claim_2 = '2. The fluid sampling system of claim 1, in which'
        response = OneClaimRequest({'pn': self.pn, 'n': 2}).serve()
        self.assertEqual(2, response['claim_num'])
        self.assertEqual(claim_2, response['claim'][:len(claim_2)])
    
    def test_raises_error_on_invalid_requests(self):
        invalid_requests = [
            {'pn': self.pn},
            {'pn': self.pn, 'n': 0},
            {'pn': self.pn, 'n': 'first'},
            {'pn': self.pn, 'n': 27},
            {'pn': self.pn, 'n': -1}
        ]
        for req_data in invalid_requests:
            with self.assertRaises(BadRequestError):
                OneClaimRequest(req_data).serve()


class TestIndependentClaimsRequestClass(unittest.TestCase):
    
    def test_get_independent_claims(self):
        pn = 'US7654321B2'
        response = IndependentClaimsRequest({'pn': pn}).serve()
        self.assertEqual(response['pn'], pn)
        self.assertEqual(6, len(response['claims']))


class TestPatentDescriptionRequestClass(unittest.TestCase):
    
    def test_get_description(self):
        pn = 'US7654321B2'
        response = PatentDescriptionRequest({'pn': pn}).serve()
        self.assertNonNullString(response['description'])

    def assertNonNullString(self, string):
        self.assertIsInstance(string, str)
        self.assertGreater(len(string.strip()), 0)


class TestCitationsRequestClass(unittest.TestCase):
    
    def test_get_citations(self):
        pn = 'US7654321B2'
        response = CitationsRequest({'pn': pn}).serve()
        self.assertIsInstance(response['citations_backward'], list)
        self.assertGreater(len(response['citations_backward']), 0)
        self.assertIsInstance(response['citations_forward'], list)
        self.assertGreater(len(response['citations_forward']), 0)


class TestBackwardCitationsRequestClass(unittest.TestCase):
    
    def test_get_back_citations(self):
        pn = 'US7654321B2'
        response = BackwardCitationsRequest({'pn': pn}).serve()
        self.assertIsInstance(response['citations_backward'], list)
        self.assertGreater(len(response['citations_backward']), 0)


class TestForwardCitationsRequestClass(unittest.TestCase):
    
    def test_get_forward_citations(self):
        pn = 'US7654321B2'
        response = ForwardCitationsRequest({'pn': pn}).serve()
        self.assertIsInstance(response['citations_forward'], list)
        self.assertGreater(len(response['citations_forward']), 0)


class TestAbstractConceptsRequestClass(unittest.TestCase):
    
    def test_get_concepts_from_abstract(self):
        pn = 'US7654321B2'
        response = AbstractConceptsRequest({'pn': pn}).serve()
        self.assertIsInstance(response['concepts'], list)
        self.assertGreater(len(response['concepts']), 0)


class TestDescriptionConceptsRequestClass(unittest.TestCase):
    
    def test_get_concepts_from_description(self):
        pn = 'US7654321B2'
        response = AbstractConceptsRequest({'pn': pn}).serve()
        self.assertIsInstance(response['concepts'], list)
        self.assertGreater(len(response['concepts']), 0)


class TestCPCsRequestClass(unittest.TestCase):
    
    def test_get_cpcs(self):
        pn = 'US7654321B2'
        response = CPCsRequest({'pn': pn}).serve()
        self.assertIsInstance(response['cpcs'], list)
        self.assertGreater(len(response['cpcs']), 0)


class TestListThumbnailsRequestClass(unittest.TestCase):
    
    def test_get_list_of_available_thumbnails(self):
        pn = 'US7654321B2'
        response = ListThumbnailsRequest({'pn': pn}).serve()
        self.assertEqual(8, len(response['thumbnails']))


class TestThumbnailRequestClass(unittest.TestCase):
    
    def test_get_a_thumbnail(self):
        req_data = {'pn': 'US7654321B2', 'n': '1'}
        response = ThumbnailRequest(req_data).serve()
        self.assertIsInstance(response, str)


class TestPatentCPCVectorRequestClass(unittest.TestCase):
    
    def test_get_cpc_patent_vector(self):
        pn = 'US7654321B2'
        response = PatentCPCVectorRequest({'pn': pn}).serve()
        self.assertIsInstance(response['vector'], list)
        self.assertEqual(256, len(response['vector']))


class TestPatentAbstractVectorRequestClass(unittest.TestCase):
    
    def test_get_abstract_text_vector(self):
        pn = 'US7654321B2'
        response = PatentAbstractVectorRequest({'pn': pn}).serve()
        self.assertIsInstance(response['vector'], list)
        self.assertEqual(768, len(response['vector']))


class TestSimilarConceptsRequestClass(unittest.TestCase):
    
    def test_get_similar_concepts_to_vehicle(self):
        response = SimilarConceptsRequest({'concept': 'vehicle'}).serve()
        self.assertIsInstance(response['similar'], list)
        self.assertGreater(len(response['similar']), 0)

    def test_return_custom_number_of_concepts(self):
        request = {'concept': 'vehicle', 'n': 13}
        response = SimilarConceptsRequest(request).serve()
        self.assertIsInstance(response['similar'], list)
        self.assertEqual(13, len(response['similar']))

    def test_raises_error_on_invalid_concept(self):
        with self.assertRaises(ResourceNotFoundError):
            SimilarConceptsRequest({'concept': 'django'}).serve()
        

class TestConceptVectorRequestClass(unittest.TestCase):
    
    def test_get_vector_for_vehicle(self):
        response = ConceptVectorRequest({'concept': 'vehicle'}).serve()
        self.assertIsInstance(response['vector'], list)
        self.assertEqual(256, len(response['vector']))

    def test_raises_error_on_invalid_concept(self):
        with self.assertRaises(ResourceNotFoundError):
            ConceptVectorRequest({'concept': 'django'}).serve()


class TestAggregatedCitationsRequest(unittest.TestCase):
    
    def test_get_one_level_citations(self):
        req_data = {'levels': 1, 'pn': 'US7654321B2'}
        response = AggregatedCitationsRequest(req_data).serve()
        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 73)

    def test_get_two_level_citations(self):
        req_data = {'levels': 2, 'pn': 'US7654321B2'}
        response = AggregatedCitationsRequest(req_data).serve()
        self.assertIsInstance(response, list)
        self.assertGreater(len(response), 73)

    def test_raises_error_if_level_parameter_missing(self):
        req_data = {'pn': 'US7654321B2'}
        with self.assertRaises(BadRequestError):
            AggregatedCitationsRequest(req_data).serve()

    def test_raises_error_if_no_level_specified(self):
        req_data = {'pn': 'US7654321B2', 'levels': None}
        with self.assertRaises(BadRequestError):
            AggregatedCitationsRequest(req_data).serve()

    def test_raises_error_if_level_out_of_range(self):
        req_data = {'levels': 5, 'pn': 'US7654321B2'}
        with self.assertRaises(BadRequestError):
            AggregatedCitationsRequest(req_data).serve()

    def test_raises_error_if_citations_grow_a_lot(self):
        req_data = {'levels': 4, 'pn': 'US7654321B2'}
        with self.assertRaises(ServerError):
            AggregatedCitationsRequest(req_data).serve()


if __name__ == '__main__':
    unittest.main()