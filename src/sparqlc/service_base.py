from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, List

from overrides import overrides
from urllib3 import HTTPResponse

from .version import VERSION

HEADER_ACCEPT = 'Accept'
HEADER_USER_AGENT = 'User-Agent'

USER_AGENT = f"sparql-client/{VERSION} +https://github.com/vlastocom/sparql-connector"

RESULT_TYPE_SPARQL_XML = 'application/sparql-results+xml'
RESULT_TYPE_SPARQL_JSON = 'application/sparql-results+json'
RESULT_TYPE_XML_SCHEMA = 'application/x-ms-access-export+xml'
RESULTS_TYPES = {
    'xml': RESULT_TYPE_SPARQL_XML,
    'xmlschema': RESULT_TYPE_XML_SCHEMA,
    'json': RESULT_TYPE_SPARQL_JSON,
}
DEFAULT_ACCEPT = RESULT_TYPE_SPARQL_XML
DEFAULT_MAX_REDIRECTS: int = 5
DEFAULT_TIMEOUT: float = 0.0
DEFAULT_ENCODING: str = 'utf-8'


class SparqlMethod(Enum):
    GET = 1
    POST = 2
    POST_URL_ENCODED = 3

    @overrides
    def __str__(self):
        return 'GET' if self is self.GET else 'POST'


class ServiceBase(object):
    PARAM_MAX_REDIRECTS = 'retries'
    PARAM_TIMEOUT = 'timeout'

    def __init__(
            self,
            method: SparqlMethod,
            endpoint: str,
            encoding: str,
            accept: str,
            max_redirects: int,
            timeout: float
    ):
        self._method: SparqlMethod = method
        self._endpoint: str = endpoint
        self._encoding: str = encoding
        self._default_graphs: List[str] = []
        self._named_graphs: List[str] = []
        self._prefix_map: Dict[str, str] = dict()
        self._headers_map: Dict[str, str] = {
            HEADER_ACCEPT: accept,
            HEADER_USER_AGENT: USER_AGENT,
        }
        self._request_kwargs: Dict[str, Any] = dict()
        self.timeout = timeout
        self.max_redirects = max_redirects

    @property
    def method(self) -> SparqlMethod:
        return self._method

    @method.setter
    def method(self, method: SparqlMethod) -> None:
        self._method = method

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @endpoint.setter
    def endpoint(self, endpoint: str) -> None:
        self._endpoint = endpoint

    @property
    def encoding(self) -> str:
        return self._encoding

    @encoding.setter
    def encoding(self, encoding: str) -> None:
        self._encoding = encoding

    @property
    def accept(self) -> str:
        return self._headers_map[HEADER_ACCEPT]

    @accept.setter
    def accept(self, accept_str: str) -> None:
        self._headers_map[HEADER_ACCEPT] = accept_str

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers_map

    @property
    def default_graphs(self) -> List[str]:
        return self._default_graphs

    @property
    def named_graphs(self) -> List[str]:
        return self._named_graphs

    def set_prefix(self, prefix: str, uri: str):
        self._prefix_map[prefix] = uri

    @property
    def prefixes(self) -> Dict[str, str]:
        return self._prefix_map

    @property
    def max_redirects(self) -> int:
        return self._request_kwargs[self.PARAM_MAX_REDIRECTS]

    @max_redirects.setter
    def max_redirects(self, max_redirects: int) -> None:
        self._request_kwargs[self.PARAM_MAX_REDIRECTS] = max_redirects

    @property
    def timeout(self) -> float:
        return self._request_kwargs[self.PARAM_TIMEOUT] if self.PARAM_TIMEOUT in self._request_kwargs else 0.0

    @timeout.setter
    def timeout(self, timeout: float) -> None:
        if timeout > 0.0:
            self._request_kwargs[self.PARAM_TIMEOUT] = timeout
        elif self.PARAM_TIMEOUT in self._request_kwargs:
            self._request_kwargs.pop(self.PARAM_TIMEOUT)

    @property
    def request_kwargs(self) -> Dict[str, Any]:
        return self._request_kwargs

    @abstractmethod
    def pool_request(self, method: SparqlMethod, url: str, **kwargs) -> HTTPResponse:
        pass
