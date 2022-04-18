from typing import cast, Tuple

import pytest

from datatypes import IRI, Literal
from datatypes_test import TestLiteral
from n3_parser import parse_n3_term


class TestN3Parsing:
    def test_parse_iri(self):
        value = 'http://example.com/some_iri'
        result = parse_n3_term(f'<{value}>')
        assert type(result) is IRI
        assert result.value == value
        i = IRI(value)
        assert parse_n3_term(i.n3()) == i

    TEST_IRI_ERROR = [
        '<http://bro.ken/iri',
        'http://bro.ken/iri>',
        '<http://bro.ken/i<ri>',
        '<http://bro.ken/i>ri>',
    ]

    @pytest.mark.parametrize('text', TEST_IRI_ERROR)
    def test_iri_error(self, text):
        with pytest.raises(ValueError):
            parse_n3_term(text)

    # noinspection SpellCheckingInspection
    STRING_LITERALS = [
                          ('""', ''),  # empty string
                          ("''", ''),  # empty string
                          ('""""""', ''),  # triple quotes (")
                          ("''''''", ''),  # triple quotes (')
                          ('" "', ' '),  # one space
                          ('"hi"', 'hi'),
                          ("'hi'", 'hi'),
                          ("'some\\ntext'", 'some\ntext'),  # newline
                          ("'some\\ttext'", 'some\ttext'),  # tab
                          ("'''some\ntext\n   with spaces'''", 'some\ntext\n   with spaces'),
                      ] + [
                          cast(Tuple[str, str], tuple(reversed(x))) for x in TestLiteral.TEST_N3
                      ]

    @pytest.mark.parametrize('n3_value, value', STRING_LITERALS)
    def test_literal(self, n3_value: str, value: str):
        result = parse_n3_term(n3_value)
        assert cast(Literal, result).lang is None
        assert cast(Literal, result).value == value
        lit = Literal(value)
        assert parse_n3_term(lit.n3()) == lit

    @pytest.mark.parametrize('n3_value, value', STRING_LITERALS)
    def test_literal_with_lang(self, n3_value: str, value: str):
        n3_value_with_lang = n3_value + '@en'
        result = parse_n3_term(n3_value_with_lang)
        assert cast(Literal, result).lang == 'en'
        assert cast(Literal, result).value == value

        lit = Literal(value, lang='en')
        assert parse_n3_term(lit.n3()) == lit

    @pytest.mark.parametrize('n3_value, value', STRING_LITERALS)
    def test_typed_literals(self, n3_value: str, value: str):
        million_uri = u'http://aims.fao.org/aos/geopolitical.owl#MillionUSD'
        n3_value_with_type = n3_value + '^^<' + million_uri + '>'
        result = parse_n3_term(n3_value_with_type)
        assert cast(Literal, result).datatype == million_uri
        assert cast(Literal, result).value == value
        lit = Literal(value, million_uri)
        assert parse_n3_term(lit.n3()) == lit

    TEST_LITERAL_ERRORS = [
        '"hello" + " world"',
        '"hello"\nx = " world"',
        'hello',
    ]

    @pytest.mark.parametrize('text', TEST_LITERAL_ERRORS)
    def test_literal_errors(self, text: str):
        with pytest.raises(ValueError):
            parse_n3_term(text)
