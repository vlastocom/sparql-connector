from decimal import Decimal
from io import IOBase
from types import TracebackType
from typing import Any, Callable, cast, Dict, Generator, IO, List, Optional, Tuple
from typing import Type
from xml.dom import pulldom
from xml.dom.pulldom import DOMEventStream
from xml.sax import SAXParseException

from dateutil.parser import parse as dt_parse

from .datatypes import BlankNode, Datatype, IRI, Literal, RDFTerm
from .datatypes import XSD_BOOLEAN, XSD_DECIMAL
from .datatypes import XSD_DATE, XSD_DATETIME, XSD_TIME
from .datatypes import XSD_DOUBLE, XSD_FLOAT, XSD_INT, XSD_INTEGER, XSD_LONG
from .exception import SparqlParseException

QUERY_ROW = Tuple[RDFTerm, ...]
DEFAULT_ENCODING = 'utf-8'


class RawResultSet:
    """
    Represents SparQL result set, which it can parse.
    """
    def __init__(self, file: IOBase, encoding: str = DEFAULT_ENCODING):
        self._variables: List[str] = []
        self._file: IOBase = file
        self._encoding: str = encoding
        self._sax_events: Optional[DOMEventStream] = None
        self._has_result: Optional[bool] = None

    def __enter__(self) -> 'RawResultSet':
        self._file.__enter__()
        return self

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType]
    ) -> bool:
        result = self._file.__exit__(exc_type, exc_val, exc_tb)
        self._close()
        return result

    def __del__(self) -> None:
        self._close()

    @property
    def closed(self) -> bool:
        return self._file is None or self._file.closed

    def check_closed(self) -> None:
        if self.closed:
            raise RuntimeError('ResultSet trying to read a closed stream')

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def variables(self) -> List[str]:
        self.start_parse()
        return self._variables

    # Maximum length of data returned by get_raw_response_text is 1MB
    MAX_RAW_LEN = 1024 * 1024

    def get_raw_response_text(self, max_length: int = MAX_RAW_LEN) -> str:
        """
        :param max_length: Maximum response length
        :return: The raw response data
        """
        try:
            return self._file.read(max_length).decode(self._encoding)  # utf-8 is the default
        finally:
            self._close()

    def start_parse(self) -> None:
        """
        Starts the parsing.

        Parses the head information and stores the columns in self.variables.
        If there are no variables in the <head>, then we also fetch
        the boolean result of ASK queries.

        Subsequent calls of this method will do nothing.
        This method does not need to be called explicitly, as has_result
        and fetch methods will call it implicitly. However, if the content
        of self.variables need to be accessed before fetching rows, call
        this method first.
        """
        if self._sax_events:
            return
        self.check_closed()
        try:
            self._sax_events = pulldom.parse(cast(IO[bytes], self._file))
            for (event, node) in self._sax_events:
                if event == pulldom.START_ELEMENT:
                    if node.tagName == 'variable':
                        self._variables.append(node.attributes['name'].value)
                    elif node.tagName == 'boolean':
                        self._sax_events.expandNode(node)
                        self._has_result = (node.firstChild.data == 'true')
                    elif node.tagName == 'result':
                        return
                elif event == pulldom.END_ELEMENT:
                    if node.tagName == 'head' and self._variables:
                        return
                    elif node.tagName == 'sparql':
                        return
        except SAXParseException as e:
            raise SparqlParseException(
                e.getMessage(),
                self.get_raw_response_text()
            ) from e

    def has_result(self) -> Optional[bool]:
        """
        ASK queries are used to test if a query would have a result.  If the
        query is an ASK query there won't be an actual result, and
        :func:`fetch_next` will return nothing. Instead, this method can be
        called to check the result from the ASK query.

        For ASK statements, True indicates the ASK query would have
        results, False indicates otherwise. If the query is a SELECT
        statement, then the return value of :func:`has_result` is
        `None`, as the XML result format doesn't tell us if there are
        any rows in the result until you have read the first one.

        :return: Result of the ASK query (True / False) or None if ASK query
                 was not executed.
        """
        self.start_parse()
        return self._has_result

    def __iter__(self):
        """
        Syntactic sugar synonym for :func:`fetch_next`.
        """
        return self.fetch_next()

    def fetch_next(self) -> Generator[QUERY_ROW, None, None]:
        """
        Fetches the next set of rows of a query result, returning a list.
        An empty list is returned when no more rows are available.
        If the query was an ASK request, then an empty list is returned as
        there are no rows available.
        """
        self.start_parse()
        idx: int = -1
        row: List[Optional[RDFTerm]] = []
        try:
            for (event, node) in self._sax_events:
                if event == pulldom.START_ELEMENT:
                    if node.tagName == 'result':
                        row = [None] * len(self._variables)
                    elif node.tagName == 'binding':
                        idx = self._variables.index(
                            node.attributes['name'].value
                        )
                    elif node.tagName == 'uri':
                        self._sax_events.expandNode(node)
                        data = ''.join(t.data for t in node.childNodes)
                        row[idx] = IRI(data)
                    elif node.tagName == 'literal':
                        self._sax_events.expandNode(node)
                        data = ''.join(t.data for t in node.childNodes)
                        lang = node.getAttribute('xml:lang') or None
                        datatype = \
                            Datatype(node.getAttribute('datatype')) or None
                        row[idx] = Literal(data, datatype, lang)
                    elif node.tagName == 'bnode':
                        self._sax_events.expandNode(node)
                        data = ''.join(t.data for t in node.childNodes)
                        row[idx] = BlankNode(data)
                elif event == pulldom.END_ELEMENT:
                    if node.tagName == 'result':
                        yield tuple(row)
        except SAXParseException as e:
            raise SparqlParseException(
                e.getMessage(),
                self.get_raw_response_text()
            ) from e

    def fetch_rows(self, limit: int = 0) -> List[QUERY_ROW]:
        """
        Fetches the rows from this query.
        :param limit: Maximum number of rows to fetch.
                      Default (0) fetches all rows.
        :return: List of fetched rows
        """
        result = []
        for row in self:
            result.append(row)
            limit -= 1
            if limit == 0:
                return result
        return result

    def _close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None


class ResultSet(RawResultSet):
    def __init__(self, file: IOBase, encoding: str = DEFAULT_ENCODING):
        super().__init__(file, encoding)

    @staticmethod
    def _parse_bool(val: str) -> bool:
        return val.lower() in ('true', '1')

    CONVERT_DICT = Dict[str, Callable[[Any], Any]]
    BASIC_TYPES: CONVERT_DICT = {
        XSD_INT: int,
        XSD_LONG: int,
        XSD_DOUBLE: float,
        XSD_FLOAT: float,
        # INTEGER is a DECIMAL, but Python `int` has no size
        # limit, so it's safe to use
        XSD_INTEGER: int,
        XSD_DECIMAL: Decimal,
        XSD_BOOLEAN: _parse_bool,
        XSD_DATETIME: dt_parse,
        XSD_DATE: lambda v: dt_parse(v).date(),
        XSD_TIME: lambda v: dt_parse(v).time(),
    }

    @classmethod
    def unpack_row(
            cls,
            raw: QUERY_ROW,
            convert_fn: Callable[[str, str], Any] = None,
            additional_types: CONVERT_DICT = None
    ) -> Tuple[Any, ...]:
        """
        Convert values in the given row from :class:`RDFTerm` objects to plain
        Python values: :class:`IRI` is converted to a unicode string containing
        the IRI value; :class:`BlankNode` is converted to a unicode string with
        the BNode's identifier, and :class:`Literal` is converted based on its
        XSD datatype.

        The library knows about common XSD types (STRING becomes :class:`unicode`,
        INTEGER and LONG become :class:`int`, DOUBLE and FLOAT become
        :class:`float`, DECIMAL becomes :class:`~decimal.Decimal`, BOOLEAN becomes
        :class:`bool`). If the `python-dateutil` library is found, then DATE,
        TIME and DATETIME are converted to :class:`~datetime.date`,
        :class:`~datetime.time` and :class:`~datetime.datetime` respectively.  For
        other conversions, an extra argument `convert` may be passed. It should be
        a callable accepting two arguments: the serialized value as a
        :class:`unicode` object, and the XSD datatype.
        """
        res = []
        known_types = dict(cls.BASIC_TYPES)
        if additional_types:
            known_types.update(additional_types)
        for item in raw:
            if item is None:
                value = None
            elif isinstance(item, Literal):
                if item.datatype in known_types:
                    value = known_types[item.datatype](item.value)
                elif convert_fn:
                    value = convert_fn(item.value, item.datatype)
                else:
                    value = item.value
            else:
                value = item.value
            res.append(value)
        return tuple(res)

    def fetch_next(self) -> Generator[QUERY_ROW, None, None]:
        """
        "Overrides" the raw generator to return values converted to python's
        native types.
        :return: Yields a tuple of values in python's native types
        """
        for raw in super().fetch_next():
            yield self.unpack_row(raw)
