import pytest

from sparqlc import BlankNode, Datatype, IRI, Literal, RDFTerm
from sparqlc.datatypes import datatype_dict


def test_datatype_none():
    dict_size = len(datatype_dict)
    assert Datatype(None) is None
    assert len(datatype_dict) == dict_size


def test_datatype_existing():
    assert Datatype(None) is None
    for dt, dt_value in datatype_dict.items():
        assert Datatype(dt) == dt_value, f'Failed for datatype {dt}'


def test_datatype_nonexistent():
    new_dt = 'My new datatype'
    assert new_dt not in datatype_dict
    assert Datatype(new_dt) == new_dt
    assert new_dt in datatype_dict
    datatype_dict.pop(new_dt)


class TestRDFTerm:
    def test_init(self):
        term = RDFTerm()
        assert term.value is None
        assert str(term) == 'None'
        with pytest.raises(NotImplementedError):
            term.n3()
        with pytest.raises(NotImplementedError):
            repr(term)

    TEST_N3_QUOTE = [
        [
            '\x01-\x08-\x09-\x0a-\x0b-\x0c-\x0d-\x0e-\x1f',
            '"\\u0001-\\u0008-\\t-\\n-\\u000b-\\u000c-\\r-\\u000e-\\u001f"'
        ],
        [
            r' !"#[\]~',
            r'" !\"#[\\]~"'
        ],
        [
            r'some "random" piece of text\string',
            '"some \\"random\\" piece of text\\\\string"'
        ],
        [
            r"singe 'quotes' work!",
            "\"singe 'quotes' work!\""
        ],
    ]

    @pytest.mark.parametrize('value, expected', TEST_N3_QUOTE)
    def test_n3_quote(self, value: str, expected: str):
        assert RDFTerm._n3_quote(value) == expected


class TestIRI:
    @pytest.mark.parametrize('value', ['', 'abc', 'ábš'])
    def test_init(self, value: str):
        term = IRI(value)
        assert term.value == value
        assert str(term) == value
        assert term.n3() == f'<{value}>'
        assert repr(term) == f'<IRI <{value}>>'

    def test_compare_with_non_iri(self):
        i1 = IRI('http://example.com/asdf')
        assert not (i1 == 'http://example.com/asdf')
        assert not (i1 == 'http://example.com/asdf')
        assert not (i1 == None)  # noqa
        assert not (i1 == 13)
        assert not (i1 == 13.0)
        assert not (i1 == ['http://example.com/asdf'])
        assert not (i1 == {
            'http://example.com/asdf': 'http://example.com/asdf'
        })


class TestLiteral:
    L1_VALUE = '1234'
    L1_TYPE = 'special_type'
    L1_LANG = 'en-gb'

    L2_VALUE = '4321'
    L2_TYPE = 'other_type'
    L2_LANG = 'en-us'

    def test_init_full(self):
        lit = Literal(self.L1_VALUE, self.L1_TYPE, self.L1_LANG)
        assert isinstance(lit, RDFTerm)
        assert lit.value == self.L1_VALUE
        assert lit.datatype == self.L1_TYPE
        assert lit.lang == self.L1_LANG
        assert str(lit) == self.L1_VALUE
        exp_n3 = f'"{self.L1_VALUE}"^^<{self.L1_TYPE}>@{self.L1_LANG}'
        assert lit.n3() == exp_n3
        assert repr(lit) == f'<Literal {exp_n3}>'

    def test_init_min(self):
        lit = Literal(self.L1_VALUE)
        assert isinstance(lit, RDFTerm)
        assert lit.value == self.L1_VALUE
        assert lit.datatype is None
        assert lit.lang is None
        assert str(lit) == self.L1_VALUE
        assert lit.n3() == f'"{self.L1_VALUE}"'
        assert repr(lit) == f'<Literal "{self.L1_VALUE}">'

    TEST_EQ = [
        [
            Literal(L1_VALUE, L1_TYPE, L1_LANG),
            Literal(L1_VALUE, L1_TYPE, L1_LANG),
            True
        ],
        [
            Literal(L1_VALUE, L1_TYPE, L1_LANG),
            Literal(L2_VALUE, L1_TYPE, L1_LANG),
            False
        ],
        [
            Literal(L1_VALUE, L1_TYPE, L1_LANG),
            Literal(L1_VALUE, L2_TYPE, L1_LANG),
            False
        ],
        [
            Literal(L1_VALUE, L1_TYPE, L1_LANG),
            Literal(L1_VALUE, L1_TYPE, L2_LANG),
            False
        ],
        [
            Literal(L1_VALUE),
            Literal(L1_VALUE),
            True
        ],
        [
            Literal(L1_VALUE),
            Literal(L2_VALUE),
            False
        ],
        [
            Literal(L1_VALUE, L1_TYPE),
            Literal(L1_VALUE),
            False
        ],
        [
            Literal(L1_VALUE, L1_TYPE, L1_LANG),
            Literal(L1_VALUE, L1_TYPE),
            False
        ],
        [
            Literal('Hello world', lang='en'),
            Literal('Hello world', lang='en-US'),
            False
        ],
    ]

    @pytest.mark.parametrize('lit1, lit2, expectation', TEST_EQ)
    def test_eq(self, lit1: RDFTerm, lit2: RDFTerm, expectation: bool):
        assert (lit1 == lit2) is expectation

    def test_compare_with_non_literal(self):
        l1 = Literal('hi')
        assert not (l1 == 'hi')
        assert not (l1 == u'hi')
        assert not (l1 == None)  # noqa
        assert not (l1 == 13)
        assert not (l1 == 13.0)
        assert not (l1 == ['hi'])
        assert not (l1 == {'hi': 'hi'})

    TEST_REPR_STR = [
        [
            Literal('Hello world'),
            '<Literal "Hello world">',
            'Hello world'
        ],
        [
            Literal('Hello world', 'http://www.w3.org/2001/XMLSchema#string'),
            '<Literal "Hello world"^^<http://www.w3.org/2001/XMLSchema#string>>',
            'Hello world'
        ],
        [
            Literal('Hello world', 'http://www.w3.org/2001/XMLSchema#string', 'en-GB'),
            '<Literal "Hello world"^^<http://www.w3.org/2001/XMLSchema#string>@en-GB>',
            'Hello world'
        ],
        [
            Literal('Hello world', lang='en-GB'),
            '<Literal "Hello world"@en-GB>',
            'Hello world'
        ],
    ]

    @pytest.mark.parametrize('lit, expected_repr, expected_str', TEST_REPR_STR)
    def test_repr_str(self, lit: Literal, expected_repr: str, expected_str: str):
        assert repr(lit) == expected_repr
        assert str(lit) == expected_str

    LIT_TYPE = 'http://www.w3.org/2001/XMLSchema#string'
    LIT_LANG = 'en-GB'
    # noinspection SpellCheckingInspection
    TEST_N3 = [
        ['', '""'],
        [' ', '" "'],
        ['hello', '"hello"'],
        ["back\\slash", '"back\\\\slash"'],
        ['quot"ed', '"quot\\"ed"'],
        ["any\"quot'es", '"any\\"quot\'es"'],
        ["new\nlines", '"new\\nlines"'],
        ["ta\tbs", '"ta\\tbs"'],
        ["ascii-unicode", '"ascii-unicode"'],
        ["̈Ünɨcøðé", '"\\u0308\\u00dcn\\u0268c\\u00f8\\u00f0\\u00e9"'],
        ["\u6f22\u5b57(kanji)", '"\\u6f22\\u5b57(kanji)"'],
    ]

    @pytest.mark.parametrize('txt, expected', TEST_N3)
    def test_n3(self, txt: str, expected: str):
        assert Literal(txt).n3() == expected
        assert Literal(txt, lang=self.LIT_LANG).n3() == f'{expected}@{self.LIT_LANG}'
        assert Literal(txt, self.LIT_TYPE).n3() == f'{expected}^^<{self.LIT_TYPE}>'
        assert Literal(
            txt, self.LIT_TYPE, self.LIT_LANG
        ).n3() == f'{expected}^^<{self.LIT_TYPE}>@{self.LIT_LANG}'


class TestBlankNode:
    def test_init(self):
        bn = BlankNode('abc')
        assert bn.value == 'abc'
        assert str(bn) == 'abc'
        assert bn.n3() == '_:abc'
        assert repr(bn) == '<BlankNode _:abc>'

    def test_eq(self):
        bn1 = BlankNode('1')
        bn2 = BlankNode('1')
        bn3 = BlankNode('3')
        iri = IRI('1')

        assert bn1 == bn2
        assert bn1 != bn3
        assert bn1 != iri
