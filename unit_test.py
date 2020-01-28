from core.snippet import extract_snippet
from core.vectorizer import SIFTextVectorizer
from core.db import get_full_text, get_patent_data
from core.indexes import get_index
from core.subclass_predictor import predict_subclasses


def test_text_embedding():
    sent = "A mobile station sends data to a base station"
    embed = SIFTextVectorizer().embed
    expected = [-0.14729856, 0.03457638, 0.00456578, 0.2679937, -0.15244815]
    calculated = embed(sent)[:5]
    for exp, cal in zip(expected, calculated):
        assert abs(exp-cal) < 0.000001


def test_snippet_extraction():
    pn = "US10263451B2"
    query = "wireless charging using magnetic induction"
    expected = "Data used to select"
    text = get_full_text(pn)
    extracted = extract_snippet(query, text)
    assert expected in extracted


def test_search():
    query = "electric vehicles"
    index_id = "H04W"
    expected = [
        "US8289012B2", "US6678505B1", "US7099633B1", "US8494563B2",
        "US7599715B2", "US9729636B2", "US8326282B2", "US9185433B2",
        "US9872154B2", "US10015679B2" ]
    index = get_index(index_id)
    embed = SIFTextVectorizer().embed
    results = index.find_similar(embed(query), dist=False)
    overlap = set(results).intersection(set(expected))
    assert overlap


def test_subclass_predictor():
    query = "wireless networks"
    preds = predict_subclasses(query)
    assert preds[0] == 'H04W'

    preds = predict_subclasses(query, limitTo=['H02J', 'H04L'])
    assert preds[0] == 'H04L'

