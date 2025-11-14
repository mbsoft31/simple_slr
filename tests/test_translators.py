from enhanced_query_script import translate_query_s2, translate_query_arxiv, translate_query_crossref

def test_translators_boolean_preservation():
    q = '("unsupervised domain adaptation" OR "test-time adaptation") AND (pest OR disease) AND (agriculture OR crop)'
    s2 = translate_query_s2(q)
    arx = translate_query_arxiv(q)
    cr = translate_query_crossref(q)
    assert '("unsupervised domain adaptation" | "test-time adaptation")' in s2
    assert " + (pest | disease)" in s2
    assert " + (agriculture | crop)" in s2
    assert 'all:("unsupervised domain adaptation")' in arx
    assert "(all:pest OR all:disease)" in arx
    assert "(all:agriculture OR all:crop)" in arx
    assert "unsupervised domain adaptation" in cr
    assert "agriculture" in cr
