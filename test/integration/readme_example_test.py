import sparqlc
from sparqlc import IRI, Literal


def test_readme_example_1() -> None:
    q = 'SELECT DISTINCT ?station, ?orbits WHERE { ' \
         '?station a <http://dbpedia.org/ontology/SpaceStation> . ' \
         '?station <http://dbpedia.org/property/orbits> ?orbits . ' \
         'FILTER(?orbits > 50000) } ORDER BY DESC(?orbits)'
    ep = 'http://dbpedia.org/sparql'
    result = sparqlc.query(ep, q, sparqlc.SparqlMethod.GET)
    assert result.variables == ['station', 'orbits']
    assert result.fetch_rows() == [
        ('http://dbpedia.org/resource/International_Space_Station', 131440),
        ('http://dbpedia.org/resource/Mir', 86331),
        ('http://dbpedia.org/resource/Salyut_7', 51917),
        ('http://dbpedia.org/resource/Kosmos_557', '~175'),
    ]


def test_readme_example1_raw() -> None:
    q = 'SELECT DISTINCT ?station, ?orbits WHERE { ' \
         '?station a <http://dbpedia.org/ontology/SpaceStation> . ' \
         '?station <http://dbpedia.org/property/orbits> ?orbits . ' \
         'FILTER(?orbits > 50000) } ORDER BY DESC(?orbits)'
    ep = 'http://dbpedia.org/sparql'
    result = sparqlc.raw_query(ep, q, sparqlc.SparqlMethod.GET)
    rows = result.fetch_rows()
    assert result.variables == ['station', 'orbits']
    assert rows == [
        (
            IRI('http://dbpedia.org/resource/International_Space_Station'),
            Literal(131440, 'http://www.w3.org/2001/XMLSchema#integer'),
        ),
        (
            IRI('http://dbpedia.org/resource/Mir'),
            Literal(86331, 'http://www.w3.org/2001/XMLSchema#integer'),
        ),
        (
            IRI('http://dbpedia.org/resource/Salyut_7'),
            Literal(51917, 'http://www.w3.org/2001/XMLSchema#integer'),
        ),
        (
            IRI('http://dbpedia.org/resource/Kosmos_557'),
            Literal('~175', None, 'en'),
        ),
    ]

