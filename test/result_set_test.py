from datetime import date, datetime, time
from decimal import Decimal
from io import IOBase
from os import path
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import cast

import pytest

from sparqlc import BlankNode, IRI, Literal, SparqlParseException, RawResultSet
from sparqlc import ResultSet, XSD_FLOAT, XSD_INTEGER, XSD_STRING


TYPE_MILLION_USD = 'http://aims.fao.org/aos/geopolitical.owl#MillionUSD'

SIMPLE_RESULT_VARS = [
    'eeaURI',
    'gdpTotal',
    'eeacode',
    'nutscode',
    'faocode',
    'gdp',
    'name',
]

SIMPLE_RESULT_RAW = [
    (
        IRI('http://rdfdata.eionet.europa.eu/eea/countries/BE'),
        Literal('471161.0', TYPE_MILLION_USD),
        Literal('BE', lang='en'),
        Literal('BE'),
        Literal('255', XSD_STRING),
        Literal('44.252934', XSD_FLOAT),
        Literal('Belgium', lang='en'),
    ),
    (
        IRI('http://rdfdata.eionet.europa.eu/eea/countries/AL'),
        Literal('12015.0', TYPE_MILLION_USD),
        Literal('AL'),
        None,
        Literal('3', XSD_STRING),
        Literal('3.808241', XSD_FLOAT),
        Literal('Albania', lang='en'),
    ),
    (
        None,
        Literal('5069000.0', TYPE_MILLION_USD),
        None,
        None,
        None,
        None,
        Literal('Japan', lang='en'),
    ),
]

SIMPLE_RESULT = [
    (
        'http://rdfdata.eionet.europa.eu/eea/countries/BE',
        '471161.0',
        'BE',
        'BE',
        '255',
        float(44.252934),
        'Belgium',
    ),
    (
        'http://rdfdata.eionet.europa.eu/eea/countries/AL',
        '12015.0',
        'AL',
        None,
        '3',
        float(3.808241),
        'Albania',
    ),
    (
        None,
        '5069000.0',
        None,
        None,
        None,
        None,
        'Japan',
    ),
]

# noinspection SpellCheckingInspection
W3C_SAMPLE_RESULT_VARS = [
    'x',
    'hpage',
    'name',
    'mbox',
    'age',
    'blurb',
    'friend',
]

W3C_SAMPLE_RESULT_RAW = [
    (
        BlankNode('r1'),
        IRI('http://work.example.org/alice/'),
        Literal('Alice'),
        Literal(''),
        None,
        Literal(
            '<p xmlns="http://www.w3.org/1999/xhtml">My name is <b>alice</b></p>',
            datatype='http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral'
        ),
        BlankNode('r2'),
    ),
    (
        BlankNode('r2'),
        IRI('http://work.example.org/bob/'),
        Literal('Bob', lang='en'),
        IRI('mailto:bob@work.example.org'),
        Literal('30', XSD_INTEGER),
        None,
        BlankNode('r1'),
    ),
]

W3C_SAMPLE_RESULT = [
    (
        'r1',
        'http://work.example.org/alice/',
        'Alice',
        '',
        None,
        '<p xmlns="http://www.w3.org/1999/xhtml">My name is <b>alice</b></p>',
        'r2',
    ),
    (
        'r2',
        'http://work.example.org/bob/',
        'Bob',
        'mailto:bob@work.example.org',
        30,
        None,
        'r1',
    ),
]


def resource(resource_name: str) -> str:
    return open(path.join(path.dirname(__file__), 'resources', resource_name), 'r').read()


def tmp_file(directory: Path, content: str = None, encoding: str = 'utf-8') -> IOBase:
    with NamedTemporaryFile(
            mode='w', encoding=encoding,
            dir=directory, prefix=__name__, suffix='.txt',
            delete=False) as fw:
        name = fw.name
        if content:
            fw.write(content)
        fw.close()
    return cast(IOBase, open(name, 'rb'))


class TestRawResultSet:
    def test_init(self, tmp_path):
        rs = RawResultSet(tmp_file(tmp_path), 'utf-16')
        assert rs.variables == []
        assert rs.closed is False
        assert rs.encoding == 'utf-16'

    def test_init_closed(self, tmp_path):
        file = tmp_file(tmp_path)
        rs = RawResultSet(file, 'utf-16')
        file.close()
        assert rs.variables == []
        assert rs.closed is True

    def test_encoding_default(self, tmp_path):
        assert RawResultSet(tmp_file(tmp_path)).encoding == 'utf-8'

    def test_get_raw_response_text(self, tmp_path):
        content = 'Hello!'
        rs = RawResultSet(tmp_file(tmp_path, content))
        assert rs.closed is False
        assert rs.get_raw_response_text() == content
        assert rs.closed is True

    def test_get_raw_response_text_encoding(self, tmp_path):
        content = 'Hello! I have been waiting for you here!'
        rs = RawResultSet(tmp_file(tmp_path, content, encoding='utf-16'), 'utf-16')
        assert rs.closed is False
        assert rs.get_raw_response_text() == content
        assert rs.closed is True

    def test_get_raw_response_text_wrong_encoding(self, tmp_path):
        content = 'Hello! I have been waiting for you here!'
        rs = RawResultSet(tmp_file(tmp_path, content, encoding='utf-8'), 'utf-16')
        assert rs.closed is False
        assert rs.get_raw_response_text() == '效汬Ⅿ䤠栠癡\u2065敢湥眠楡楴杮映牯礠畯栠牥Ⅵ'
        assert rs.closed is True

    def test_get_raw_response_text_max_length(self, tmp_path):
        content = 'Hello! I have been waiting for you here!'
        length = 6
        rs = RawResultSet(tmp_file(tmp_path, content))
        assert rs.closed is False
        assert rs.get_raw_response_text(length) == content[:length]
        assert rs.closed is True

    def test_with(self, tmp_path):
        with RawResultSet(tmp_file(tmp_path)) as rs:
            assert rs.closed is False
        assert rs.closed is True

    def test_has_response_neutral(self, tmp_path):
        assert RawResultSet(tmp_file(tmp_path)).has_result() is None

    def test_has_response_negative(self, tmp_path):
        assert RawResultSet(tmp_file(tmp_path, resource('ask_result_negative.srx'))).has_result() is False

    def test_has_response_positive(self, tmp_path):
        assert RawResultSet(tmp_file(tmp_path, resource('ask_result_positive.srx'))).has_result() is True

    def test_start_parse(self, tmp_path):
        rs = RawResultSet(tmp_file(tmp_path, resource('simple_result.srx')))
        assert rs.variables == []
        rs.start_parse()
        assert rs.variables == SIMPLE_RESULT_VARS

    def test_simple_query_fetch_rows(self, tmp_path):
        rs = RawResultSet(tmp_file(tmp_path, resource('simple_result.srx')))
        assert rs.fetch_rows() == SIMPLE_RESULT_RAW
        assert rs.variables == SIMPLE_RESULT_VARS

    def test_simple_query_fetch_limited(self, tmp_path):
        rs = RawResultSet(tmp_file(tmp_path, resource('simple_result.srx')))
        assert rs.fetch_rows(2) == SIMPLE_RESULT_RAW[:2]
        assert rs.variables == SIMPLE_RESULT_VARS

    def test_simple_query_fetch_iter(self, tmp_path):
        rs = RawResultSet(tmp_file(tmp_path, resource('simple_result.srx')))
        idx = 0
        for row in rs:
            assert row == SIMPLE_RESULT_RAW[idx]
            idx += 1
        assert rs.variables == SIMPLE_RESULT_VARS

    def test_ask_result_not_failing_fetch(self, tmp_path):
        rs = RawResultSet(tmp_file(tmp_path, resource('ask_result_positive.srx')))
        rows = rs.fetch_rows()
        assert len(rows) == 0

    def test_w3_result(self, tmp_path):
        rs = RawResultSet(tmp_file(tmp_path, resource('w3c_sample_result.srx')))
        assert rs.fetch_rows() == W3C_SAMPLE_RESULT_RAW
        assert rs.variables == W3C_SAMPLE_RESULT_VARS

    def test_utf_8(self, tmp_path):
        r = RawResultSet(tmp_file(tmp_path, resource('utf_8_result.srx'))).fetch_rows()
        assert r == [(
            IRI('http://aims.fao.org/aos/geopolitical.owl#Germany'),
            Literal('Germany', XSD_STRING),
            Literal('Германия', XSD_STRING),
        )]

    def test_invalid_chars(self, tmp_path):
        with pytest.raises(SparqlParseException):
            RawResultSet(tmp_file(tmp_path, resource('invalid_chars.srx'))).fetch_rows()


class TestResultSet:
    def test_simple_query_fetch_rows(self, tmp_path):
        rs = ResultSet(tmp_file(tmp_path, resource('simple_result.srx')))
        assert rs.fetch_rows() == SIMPLE_RESULT
        assert rs.variables == SIMPLE_RESULT_VARS

    def test_simple_query_fetch_limited(self, tmp_path):
        rs = ResultSet(tmp_file(tmp_path, resource('simple_result.srx')))
        assert rs.fetch_rows(2) == SIMPLE_RESULT[:2]
        assert rs.variables == SIMPLE_RESULT_VARS

    def test_simple_query_fetch_iter(self, tmp_path):
        rs = ResultSet(tmp_file(tmp_path, resource('simple_result.srx')))
        idx = 0
        for row in rs:
            assert row == SIMPLE_RESULT[idx]
            idx += 1
        assert rs.variables == SIMPLE_RESULT_VARS

    def test_ask_result_not_failing_fetch(self, tmp_path):
        rs = ResultSet(tmp_file(tmp_path, resource('ask_result_positive.srx')))
        rows = rs.fetch_rows()
        assert len(rows) == 0

    def test_w3_result(self, tmp_path):
        rs = ResultSet(tmp_file(tmp_path, resource('w3c_sample_result.srx')))
        assert rs.fetch_rows() == W3C_SAMPLE_RESULT
        assert rs.variables == W3C_SAMPLE_RESULT_VARS

    def test_utf_8(self, tmp_path):
        r = ResultSet(tmp_file(tmp_path, resource('utf_8_result.srx'))).fetch_rows()
        assert r == [(
            'http://aims.fao.org/aos/geopolitical.owl#Germany',
            'Germany',
            'Германия',
        )]

    def test_big_text(self, tmp_path):
        """
        `xml.dom.pulldom` may return several text nodes within a single
        binding. This seems to be triggered especially by entities,
        e.g. "&lt;".
        """
        r = ResultSet(tmp_file(tmp_path, resource('big_text.srx'))).fetch_rows()
        assert r == [(
            'multiple<br>paragraphs<br>here',
            'http://example.com/',
            'bnode.id'
        )]

    def test_conversions(self, tmp_path):
        """
        Test the remainder of conversions
        """
        r = ResultSet(tmp_file(tmp_path, resource('xsd_types.srx'))).fetch_rows()
        assert r == [(
            'Estonia',
            Decimal('123.456'),
            datetime(2009, 11, 0o2, 14, 31, 40),
            date(1991, 8, 20),
            time(18, 58, 21),
        )]

    def test_unpack_row_conversion_fn(self):
        def convert_fn(value: str, new_type: str) -> str:
            return f'{value}:{new_type}'

        raw = (Literal('123', datatype='typeX'),)
        assert ResultSet.unpack_row(raw, convert_fn) == ('123:typeX',)

    def test_unpack_row_additional_type(self):
        extras = {'typeX': float}
        raw = (Literal('123', datatype='typeX'),)
        assert ResultSet.unpack_row(raw, additional_types=extras) == (123.0,)
