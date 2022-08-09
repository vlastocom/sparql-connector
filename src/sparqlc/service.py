from base64 import encodebytes

from urllib3 import HTTPResponse, PoolManager

from .query import Query
from .result_set import RawResultSet, ResultSet
from .service_base import DEFAULT_ACCEPT, ServiceBase
from .service_base import DEFAULT_ENCODING, DEFAULT_MAX_REDIRECTS, DEFAULT_TIMEOUT, RESULT_TYPE_SPARQL_XML, SparqlMethod


class Service(ServiceBase):
    """
    This is the main entry to the library.
    The user creates a :class:`Service`, then sends a query to it.
    If we want to have persistent connections, then open them here.
    """

    def __init__(
            self,
            endpoint: str,
            method: SparqlMethod = SparqlMethod.POST,
            encoding: str = DEFAULT_ENCODING,
            accept: str = DEFAULT_ACCEPT,
            max_redirects: int = DEFAULT_MAX_REDIRECTS,
            timeout: float = DEFAULT_TIMEOUT):
        super().__init__(method, endpoint, encoding, accept, max_redirects, timeout)
        self._pool_manager = PoolManager()

    def create_query(self) -> Query:
        return Query(self)

    def query(self, query_str: str) -> ResultSet:
        """
        Executes the query and returns the result
        :param query_str: Query string
        :return:
        """
        return self.create_query().query(query_str)

    def raw_query(self, query_str: str) -> RawResultSet:
        """
        Executes the query and returns the raw results consisting of the actual Sparql objects
        :param query_str: Query string
        :return:
        """
        return self.create_query().raw_query(query_str)

    def authenticate(self, username, password):
        b64_encoded = encodebytes(bytes(f"{username}:{password}")).replace(bytes("\012"), bytes())
        self._headers_map['Authorization'] = f"Basic {b64_encoded}"

    def pool_request(self, method: SparqlMethod, url: str, **kwargs) -> HTTPResponse:
        return self._pool_manager.request(str(method), url, **kwargs)


def query(endpoint: str,
          query_str: str,
          method: SparqlMethod = SparqlMethod.POST,
          encoding: str = DEFAULT_ENCODING,
          accept: str = RESULT_TYPE_SPARQL_XML,
          max_redirects: int = DEFAULT_MAX_REDIRECTS,
          timeout: float = DEFAULT_TIMEOUT) -> ResultSet:
    """
    Convenient method to execute a single query.
    Exactly equivalent to:
        sparql.Service(endpoint).query(query)
    Only use it for one-off queries, as it manages the thread pool.
    If you need multitude of queries, create a service once and use it repeatedly.

    :param endpoint: HTTP endpoint to run the query against
    :param query_str: Query string
    :param method: Query method (e.g. GET, POST). Default: POST
    :param encoding: Encoding of the query string. Default: utf-8
    :param accept: Accept header, defining the result format. Default: sparql-results+xml
    :param max_redirects: Maximum number of redirections before the error is thrown
    :param timeout: Timeout in seconds
    :return: The result of the query
    """
    return Service(endpoint, method, encoding, accept, max_redirects, timeout).query(query_str)


def raw_query(endpoint: str,
              query_str: str,
              method: SparqlMethod = SparqlMethod.POST,
              encoding: str = DEFAULT_ENCODING,
              accept: str = RESULT_TYPE_SPARQL_XML,
              max_redirects: int = DEFAULT_MAX_REDIRECTS,
              timeout: float = DEFAULT_TIMEOUT) -> RawResultSet:
    """
    Convenient method to execute a single query, returning RawResultSet instead of ResultSet.
    Exactly equivalent to:
        sparql.Service(endpoint).query(query)
    Only use it for one-off queries, as it manages the thread pool.
    If you need multitude of queries, create a service once and use it repeatedly.

    :param endpoint: HTTP endpoint to run the query against
    :param query_str: Query string
    :param method: Query method (e.g. GET, POST). Default: POST
    :param encoding: Encoding of the query string. Default: utf-8
    :param accept: Accept header, defining the result format. Default: sparql-results+xml
    :param max_redirects: Maximum number of redirections before the error is thrown
    :param timeout: Timeout in seconds
    :return: The result of the query
    """
    return Service(endpoint, method, encoding, accept, max_redirects, timeout).raw_query(query_str)
