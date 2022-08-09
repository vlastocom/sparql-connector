from typing import cast

import pytest

from sparqlc import query, SparqlMethod


class TestQueryIntegration:
    ORDNANCE_SURVEY_ENDPOINT = 'https://data.ordnancesurvey.co.uk/datasets/os-linked-data/apis/sparql'
    ORDNANCE_SURVEY_QUERY = """
        PREFIX spatial: <http://data.ordnancesurvey.co.uk/ontology/spatialrelations/>
        
        SELECT ?postcode
        WHERE {
        ?postcode spatial:within <http://data.ordnancesurvey.co.uk/id/postcodearea/RG>.
        }
        LIMIT 20
        OFFSET 0
    """

    @pytest.mark.parametrize('method', [m for m in SparqlMethod])
    def test_ordnance_survey_query(self, method: SparqlMethod):
        """
        Not all publicly available datasets support all HTTP/SPARQL methods.
        British Ordnance Survey does, so we use it to test all methods and get some postcodes
        :param method: Sparql method which we are running this test with
        """
        q = query(
            self.ORDNANCE_SURVEY_ENDPOINT,
            self.ORDNANCE_SURVEY_QUERY,
            method=method
        )
        rows = q.fetch_rows()
        assert len(rows) == 20
        assert all([cast(str, r[0]).startswith('http://data.ordnancesurvey.co.uk/id/postcodeunit/RG') for r in rows])

    ORDNANCE_SURVEY_LONG_QUERY = """
        PREFIX spatial: <http://data.ordnancesurvey.co.uk/ontology/spatialrelations/>

        SELECT ?postcode
        WHERE {
        ?postcode spatial:within <http://data.ordnancesurvey.co.uk/id/postcodearea/RG>.
        }
    """

    def test_ordnance_survey_long_query(self):
        """
        A large version of the Ordnance Survey query brings back more than 23,000 postcodes from Reading district.
        """
        q = query(
            self.ORDNANCE_SURVEY_ENDPOINT,
            self.ORDNANCE_SURVEY_LONG_QUERY,
            method=SparqlMethod.GET
        )
        rows = q.fetch_rows()
        assert len(rows) > 23000
        assert all(
            [
                cast(str, r[0]).startswith('http://data.ordnancesurvey.co.uk/id/postcodeunit/RG')
                or cast(str, r[0]).startswith('http://data.ordnancesurvey.co.uk/id/postcodedistrict/RG')
                for r in rows
            ]
        )

    ENDPOINT_DBPEDIA = 'http://dbpedia.org/sparql'
    SMALL_QUERY = '''
        SELECT *
        WHERE
        {
          ?athlete  rdfs:label      "Cristiano Ronaldo"@en ;
                    dbo:birthPlace  ?place .
         ?place     a               dbo:City ;
                    rdfs:label      ?cityName .
        }    
    '''

    def test_small_query(self):
        """
        Test a small source of knowledge on Cristiano Ronaldo from DBPedia.
        """
        q = query(
            self.ENDPOINT_DBPEDIA,
            self.SMALL_QUERY,
            method=SparqlMethod.GET
        )
        rows = q.fetch_rows()
        assert len(rows) >= 21
        assert all([r[0] == 'http://dbpedia.org/resource/Cristiano_Ronaldo' for r in rows])
        assert all([r[1] == 'http://dbpedia.org/resource/Funchal' for r in rows])

    ENDPOINT_SCHOLARLY_DATA = 'http://www.scholarlydata.org/sparql/'
    LARGE_QUERY = '''
        PREFIX person: <https://w3id.org/scholarlydata/person/>
        PREFIX conf: <https://w3id.org/scholarlydata/ontology/conference-ontology.owl#>
        SELECT DISTINCT ?paper ?title ?person ?name
        WHERE{
          ?paper a conf:InProceedings;
            conf:hasAuthorList ?authorList;
            conf:title ?title . 
          ?authorList conf:hasFirstItem ?item .
          ?item conf:hasContent ?person .
          ?person conf:name ?name
        }
        '''

    def test_large_response(self):
        """
        A large list of scientific papers from ScholarlyData (more than 2.5MB of them)
        """
        q = query(
            self.ENDPOINT_SCHOLARLY_DATA,
            self.LARGE_QUERY,
            method=SparqlMethod.GET
        )
        rows = q.fetch_rows()
        assert len(rows) >= 5950
        one_row = list(filter(
            lambda r: r[0] == 'https://w3id.org/scholarlydata/inproceedings/iswc2005/proceedings/paper-39',
            rows
        ))
        assert one_row == [
            (
                'https://w3id.org/scholarlydata/inproceedings/iswc2005/proceedings/paper-39',
                'On Identifying Knowledge Processing Requirements',
                'https://w3id.org/scholarlydata/person/alain-leger',
                'Alain Léger'
            ),
            (
                'https://w3id.org/scholarlydata/inproceedings/iswc2005/proceedings/paper-39',
                'On Identifying Knowledge Processing Requirements',
                'https://w3id.org/scholarlydata/person/alain-leger',
                'Alain Leger'
            )
        ]
