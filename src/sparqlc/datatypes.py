import re
from abc import abstractmethod
from typing import Any, Optional

# The purpose of this construction is to use shared strings when
# they have the same value. This way comparisons can happen on the
# memory address rather than looping through the content.
XSD_STRING = 'http://www.w3.org/2001/XMLSchema#string'
XSD_INT = 'http://www.w3.org/2001/XMLSchema#int'
XSD_LONG = 'http://www.w3.org/2001/XMLSchema#long'
XSD_DOUBLE = 'http://www.w3.org/2001/XMLSchema#double'
XSD_FLOAT = 'http://www.w3.org/2001/XMLSchema#float'
XSD_INTEGER = 'http://www.w3.org/2001/XMLSchema#integer'
XSD_DECIMAL = 'http://www.w3.org/2001/XMLSchema#decimal'
XSD_DATETIME = 'http://www.w3.org/2001/XMLSchema#dateTime'
XSD_DATE = 'http://www.w3.org/2001/XMLSchema#date'
XSD_TIME = 'http://www.w3.org/2001/XMLSchema#time'
XSD_BOOLEAN = 'http://www.w3.org/2001/XMLSchema#boolean'

datatype_dict = {
    '': '',
    XSD_STRING: XSD_STRING,
    XSD_INT: XSD_INT,
    XSD_LONG: XSD_LONG,
    XSD_DOUBLE: XSD_DOUBLE,
    XSD_FLOAT: XSD_FLOAT,
    XSD_INTEGER: XSD_INTEGER,
    XSD_DECIMAL: XSD_DECIMAL,
    XSD_DATETIME: XSD_DATETIME,
    XSD_DATE: XSD_DATE,
    XSD_TIME: XSD_TIME,
    XSD_BOOLEAN: XSD_BOOLEAN
}


# noinspection PyPep8Naming
def Datatype(value):
    """
    Replace the string with a shared string.
    intern() only works for plain strings - not unicode.
    We make it look like a class, because it conceptually could be.
    """
    if value is None:
        r = None
    elif value in datatype_dict:
        r = datatype_dict[value]
    else:
        r = datatype_dict[value] = value
    return r


class RDFTerm:
    """
    Super class containing methods to override. :class:`IRI`,
    :class:`Literal` and :class:`BlankNode` all inherit from :class:`RDFTerm`.
    """
    __allow_access_to_unprotected_subobjects__ = {'n3': 1}

    def __init__(self, value: str = None):
        self.value: Optional[str] = value

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other) -> bool:
        return type(self) == type(other) and self.value == other.value

    @abstractmethod
    def n3(self) -> str:
        """
        :return: A Notation3 representation of this term
        """
        raise NotImplementedError('Subclasses of RDFTerm must implement `n3`')

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.n3()}>'

    # Matches everything outside 0x20 - 0x7e, plus double quote and backslash
    # See N-Triples syntax: http://www.w3.org/TR/rdf-testcases/#ntriples
    _chars_to_escape = re.compile(r'[^ -~]|["\\]')
    _n3_quote_map = {
        '\t': r'\t',
        '\n': r'\n',
        '\r': r'\r',
        '"': r'\"',
        '\\': r'\\',
    }

    @classmethod
    def _n3_quote(cls, txt: str):
        def escape(m):
            ch = m.group()
            code = ord(ch)
            if ch in cls._n3_quote_map:
                return cls._n3_quote_map[ch]
            if 0x20 <= code < 0x7f:
                # We should not be hitting this (thanks to re)
                return ch
            if code < 0x10000:
                return f'\\u{ord(ch):04x}'
            return f'\\U{ord(ch):08x}'

        return '"' + cls._chars_to_escape.sub(escape, txt) + '"'


class IRI(RDFTerm):
    """ An RDF resource. """
    def __init__(self, value: str):
        super().__init__(value)

    def n3(self) -> str:
        return f'<{self.value}>'


class Literal(RDFTerm):
    """
    Literals. These can take a data type or a language code.
    """
    def __init__(self, value: Any, datatype: str = None, lang: str = None):
        super().__init__(str(value))
        self.lang = lang
        self.datatype = datatype

    def __eq__(self, other):
        return type(self) == type(other) and \
               self.value == other.value and \
               self.lang == other.lang and \
               self.datatype == other.datatype

    def n3(self) -> str:
        n3_value = self._n3_quote(self.value)
        n3_type = f'^^<{self.datatype}>' if self.datatype is not None else ''
        n3_lang = f'@{self.lang}' if self.lang is not None else ''
        return f'{n3_value}{n3_type}{n3_lang}'


class BlankNode(RDFTerm):
    """ Blank node. Similar to `IRI` but lacks a stable identifier. """
    def __init__(self, value):
        super().__init__(value)

    def n3(self):
        return f'_:{self.value}'
