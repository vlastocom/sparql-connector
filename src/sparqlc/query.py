from copy import deepcopy
from typing import Dict, Optional
from urllib.parse import urlencode

from urllib3 import HTTPResponse
from urllib3.exceptions import HTTPError

from .exception import SparqlException, SparqlProtocolException
from .result_set import RawResultSet, ResultSet
from .service_base import ServiceBase, SparqlMethod


class Query(ServiceBase):
    def __init__(self, service: ServiceBase):
        super().__init__(
            service.method,
            service.endpoint,
            service.encoding,
            service.accept,
            service.max_redirects,
            service.timeout
        )
        self._default_graphs = deepcopy(service._default_graphs)
        self._headers_map = deepcopy(service._headers_map)
        self._named_graphs = deepcopy(service._named_graphs)
        self._prefix_map = deepcopy(service._prefix_map)
        self._request_kwargs = deepcopy(service._request_kwargs)
        self._service = service

    @property
    def service(self) -> ServiceBase:
        return self._service

    def query(self, statement: str) -> ResultSet:
        """
        Sends the statement and starts parsing the response.
        :param statement: SPARQL statement to send
        :return: ResultSet allowing to parse the response
        """
        return ResultSet(self._query(statement), self.encoding)

    def raw_query(self, statement: str) -> RawResultSet:
        """
        Sends the statement and starts parsing the response to raw types.
        :param statement: SPARQL statement to send
        :return: RawResultSet allowing to parse the response
        """
        return RawResultSet(self._query(statement), self.encoding)

    def _query(self, statement: str) -> HTTPResponse:
        """
        Sends the statement and receives the response. Handles HTTP errors.
        :param statement: SPARQL statement to send
        :return: ResultSet allowing to parse the response
        """
        try:
            response = self.pool_request(
                self.method,
                self.query_uri(statement),
                headers=self.headers | self.content_type_header(),
                body=self.query_body(statement),
                preload_content=False,
                **self.request_kwargs
            )
            if response.status == 200:
                return response
            else:
                msg = response.read().decode(self.encoding)
                response.close()
                raise SparqlProtocolException(response.status, msg)
        except HTTPError as http_error:
            raise SparqlException(f'HTTP Error occurred.') from http_error

    def pool_request(self, method: SparqlMethod, url: str, **kwargs) -> HTTPResponse:
        return self._service.pool_request(method, url, **kwargs)

    CONTENT_TYPE_HEADER = 'Content-Type'
    CONTENT_TYPE_POST_URLENCODED = 'application/x-www-form-urlencoded'
    CONTENT_TYPE_POST = 'application/sparql-query'
    REQUEST_CONTENT_TYPE_MAP = {
        SparqlMethod.GET: None,
        SparqlMethod.POST: CONTENT_TYPE_POST,
        SparqlMethod.POST_URL_ENCODED: CONTENT_TYPE_POST_URLENCODED,
    }

    def content_type_header(self) -> Dict[str, str]:
        ct = self.REQUEST_CONTENT_TYPE_MAP.get(self.method, None)
        return {self.CONTENT_TYPE_HEADER: ct} if ct else dict()

    def query_body(self, statement: str) -> Optional[bytes]:
        match self.method:
            case SparqlMethod.GET:
                return None
            case SparqlMethod.POST_URL_ENCODED:
                return self.param_string(statement).encode(self.encoding)
            case _:
                return self.query_string(statement).encode(self.encoding)

    def query_uri(self, statement: str) -> str:
        """
        Creates a fully fledged query URI to be used in HTTP request.
        The result depends on the SparqlMethod chosen and the params.

        :param statement: Statement to turn into query
        :return: URI for the HTTP request
        """
        endpoint = self.endpoint.strip()
        if self.method is SparqlMethod.POST_URL_ENCODED:
            return endpoint
        separator = '&' if '?' in self.endpoint else '?'
        qs = self.param_string(statement if self.method is SparqlMethod.GET else None)
        return endpoint + separator + qs if qs else endpoint

    def param_string(self, statement: str | None) -> str:
        """
        Creates a url-encoded parameter string, containing query, graph URIs
        :param statement: Statement to turn into query (or None if query should be omitted)
        :return: Query part of the URI string corresponding to query, prefixes, graph URIs
        """
        graph_params = \
            [('default-graph-uri', uri.encode(self.encoding)) for uri in self.default_graphs] \
            + [('named-graph-uri', uri.encode(self.encoding)) for uri in self.named_graphs]

        if statement:
            return urlencode([('query', self.query_string(statement).encode(self.encoding))] + graph_params)
        else:
            return urlencode(graph_params)

    def query_string(self, statement: str) -> str:
        """
        Turns a SPARQL statement into a fully-fledged query by decorating it with prefixes
        :param statement: SPARQL statement
        :return: Query string corresponding with the statement, decorated with prefixes
        """
        prefixes = ' '.join([
            f"PREFIX {p}: <{self._prefix_map[p]}>"
            for p in self._prefix_map
        ])
        if len(prefixes) > 0:
            prefixes += ' '
        return prefixes + statement
