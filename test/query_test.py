from urllib.parse import quote_plus, urlencode
from typing import List
from unittest.mock import MagicMock

import pytest
from urllib3 import HTTPResponse
from urllib3.exceptions import ConnectTimeoutError

from service_mixin_test import MyService
from sparqlc import Query, RawResultSet, ResultSet, SparqlException, SparqlMethod, SparqlProtocolException
from sparqlc.service_base import HEADER_ACCEPT, HEADER_USER_AGENT, USER_AGENT


# noinspection SqlDialectInspection,SqlNoDataSourceInspection
class TestQuery:
    class MyTestService(MyService):
        def __init__(self, method: SparqlMethod = SparqlMethod.POST):
            super().__init__(0.0)
            self.encoding = self.SVC_DEFAULT_ENCODING
            self.method = method

        SVC_DEFAULT_ENCODING = 'utf-8'
        SVC_DEFAULT_GRAPHS = ['G1', 'G2', 'G3']
        SVC_NAMED_GRAPHS = ['NG1', 'NG2']

        @classmethod
        def get_fixture(cls, method: SparqlMethod) -> 'TestQuery.MyTestService':
            svc = cls.__new__(cls)
            svc.__init__(method)
            svc.default_graphs.extend(cls.SVC_DEFAULT_GRAPHS)
            svc.named_graphs.extend(cls.SVC_NAMED_GRAPHS)
            svc.endpoint = cls.ENDPOINT
            return svc

    DEFAULT_HEADERS = {
        HEADER_ACCEPT: MyService.ACCEPT,
        HEADER_USER_AGENT: USER_AGENT
    }

    def test_init(self):
        service = MyService(MyService.TIMEOUT)
        q = Query(service)
        assert q.method is MyService.METHOD
        assert q.accept == MyService.ACCEPT
        assert q.endpoint == MyService.ENDPOINT
        assert q.encoding == MyService.ENCODING
        assert q.headers == self.DEFAULT_HEADERS
        assert q.default_graphs == []
        assert q.named_graphs == []
        assert q.prefixes == dict()
        assert q.max_redirects == MyService.MAX_REDIRECTS
        assert q.timeout == MyService.TIMEOUT
        assert q.request_kwargs == {
            MyService.PARAM_TIMEOUT: MyService.TIMEOUT,
            MyService.PARAM_MAX_REDIRECTS: MyService.MAX_REDIRECTS,
        }
        assert q.service is service

    def test_init_deepcopy(self):
        service = MyService(0.0)
        service.named_graphs.append('123')
        service.default_graphs.append('456')
        service.set_prefix('a', '1')
        service.request_kwargs['something_new'] = 123456

        q = Query(service)

        assert q.headers == service.headers
        assert q.headers is not service.headers

        assert q.default_graphs == service.default_graphs
        assert q.default_graphs is not service.default_graphs

        assert q.named_graphs == service.named_graphs
        assert q.named_graphs is not service.named_graphs

        assert q.prefixes == service.prefixes
        assert q.prefixes is not service.prefixes

        assert q.request_kwargs == service.request_kwargs
        assert q.request_kwargs is not service.request_kwargs

        assert q.service is service

    def test_query_fail(self):
        method = SparqlMethod.GET
        endpoint = 'http://a.b/c'
        statement = 'Hello'
        error_code = 500
        error_message = 'Error occurred'

        mock_response = MagicMock(spec=HTTPResponse, name="Mock response")
        mock_response.status = error_code
        mock_response.read.return_value = error_message.encode()
        service = self.MyTestService(method)
        service.endpoint = endpoint
        service.pool_request = MagicMock(return_value=mock_response)

        with pytest.raises(SparqlProtocolException) as exc_info:
            Query(service).query(statement)

        assert exc_info.value.code == 500
        assert exc_info.value.message.index(error_message) >= 0
        service.pool_request.assert_called_once_with(
            method,
            f'{endpoint}?query={statement}',
            headers=self.DEFAULT_HEADERS,
            body=None,
            preload_content=False,
            retries=MyService.MAX_REDIRECTS
        )

    REQUEST_STATEMENT = 'Hello measly world'
    RESPONSE_HTTP_STATUS = 200
    RESPONSE_HTTP_BODY = 'We are not parsing this'

    def mock_response_fixture(self) -> HTTPResponse:
        mock_response = MagicMock(spec=HTTPResponse, name="Mock response")
        mock_response.status = self.RESPONSE_HTTP_STATUS
        mock_response.read.return_value = self.RESPONSE_HTTP_BODY.encode()
        return mock_response

    @staticmethod
    def default_graph_params(graphs: List[str]) -> str:
        return '&' + str.join('&', map(lambda elem: f'default-graph-uri={elem}', graphs))

    @staticmethod
    def named_graph_params(graphs: List[str]) -> str:
        return '&' + str.join('&', map(lambda elem: f'named-graph-uri={elem}', graphs))

    def test_query_success_get(self):
        method = SparqlMethod.GET
        svc = self.MyTestService.get_fixture(method)
        svc.pool_request = MagicMock(return_value=self.mock_response_fixture())
        result_set = Query(svc).query(self.REQUEST_STATEMENT)
        assert type(result_set) is ResultSet
        assert result_set.get_raw_response_text() == self.RESPONSE_HTTP_BODY

        query_params = [
            ('query', self.REQUEST_STATEMENT),
            ('default-graph-uri', self.MyTestService.SVC_DEFAULT_GRAPHS),
            ('named-graph-uri', self.MyTestService.SVC_NAMED_GRAPHS),
        ]

        expected_query = self.MyTestService.ENDPOINT + '?' + urlencode(
            query_params, doseq=True, encoding=self.MyTestService.SVC_DEFAULT_ENCODING
        )

        svc.pool_request.assert_called_once_with(
            method,
            expected_query,
            headers=self.DEFAULT_HEADERS,
            body=None,
            preload_content=False,
            retries=MyService.MAX_REDIRECTS
        )

    def test_query_success_post(self):
        method = SparqlMethod.POST
        svc = self.MyTestService.get_fixture(method)
        svc.pool_request = MagicMock(return_value=self.mock_response_fixture())
        result_set = Query(svc).query(self.REQUEST_STATEMENT)
        assert type(result_set) is ResultSet
        assert result_set.get_raw_response_text() == self.RESPONSE_HTTP_BODY

        query_params = [
            ('default-graph-uri', self.MyTestService.SVC_DEFAULT_GRAPHS),
            ('named-graph-uri', self.MyTestService.SVC_NAMED_GRAPHS),
        ]

        expected_query = self.MyTestService.ENDPOINT + '?' + urlencode(
            query_params, doseq=True, encoding=self.MyTestService.SVC_DEFAULT_ENCODING
        )

        expected_request_body = self.REQUEST_STATEMENT
        expected_headers = self.DEFAULT_HEADERS.copy()
        expected_headers.update({'Content-Type': 'application/sparql-query'})

        svc.pool_request.assert_called_once_with(
            method,
            expected_query,
            headers=expected_headers,
            body=expected_request_body.encode(self.MyTestService.SVC_DEFAULT_ENCODING),
            preload_content=False,
            retries=MyService.MAX_REDIRECTS
        )

    def test_query_success_post_url_encoded(self):
        method = SparqlMethod.POST_URL_ENCODED
        svc = self.MyTestService.get_fixture(method)
        svc.pool_request = MagicMock(return_value=self.mock_response_fixture())
        result_set = Query(svc).query(self.REQUEST_STATEMENT)
        assert type(result_set) is ResultSet
        assert result_set.get_raw_response_text() == self.RESPONSE_HTTP_BODY

        expected_query = self.MyTestService.ENDPOINT

        body_params = [
            ('query', self.REQUEST_STATEMENT),
            ('default-graph-uri', self.MyTestService.SVC_DEFAULT_GRAPHS),
            ('named-graph-uri', self.MyTestService.SVC_NAMED_GRAPHS),
        ]

        expected_request_body = urlencode(body_params, doseq=True, encoding=self.MyTestService.SVC_DEFAULT_ENCODING)
        expected_headers = self.DEFAULT_HEADERS.copy()
        expected_headers.update({'Content-Type': 'application/x-www-form-urlencoded'})

        svc.pool_request.assert_called_once_with(
            method,
            expected_query,
            headers=expected_headers,
            body=expected_request_body.encode(self.MyTestService.SVC_DEFAULT_ENCODING),
            preload_content=False,
            retries=MyService.MAX_REDIRECTS
        )

    def test_query_exception(self):
        method = SparqlMethod.GET
        endpoint = 'http://a.b/c'
        statement = 'Hello'
        exception = ConnectTimeoutError()

        service = self.MyTestService(method)
        service.endpoint = endpoint
        service.pool_request = MagicMock(side_effect=exception)

        with pytest.raises(SparqlException) as exc_info:
            Query(service).query(statement)

        assert exc_info.value.message.index('HTTP Error') == 0
        assert exc_info.value.__cause__ is exception
        service.pool_request.assert_called_once_with(
            method,
            f'{endpoint}?query={statement}',
            headers=self.DEFAULT_HEADERS,
            body=None,
            preload_content=False,
            retries=MyService.MAX_REDIRECTS
        )

    def test_raw_query_fail(self):
        method = SparqlMethod.GET
        endpoint = 'http://a.b/c'
        statement = 'Hello'
        error_code = 500
        error_message = 'Error occurred'

        mock_response = MagicMock(spec=HTTPResponse, name="Mock response")
        mock_response.status = error_code
        mock_response.read.return_value = error_message.encode()
        service = self.MyTestService(method)
        service.endpoint = endpoint
        service.pool_request = MagicMock(return_value=mock_response)

        with pytest.raises(SparqlProtocolException) as exc_info:
            Query(service).raw_query(statement)

        assert exc_info.value.code == 500
        assert exc_info.value.message.index(error_message) >= 0
        service.pool_request.assert_called_once_with(
            method,
            f'{endpoint}?query={statement}',
            headers=self.DEFAULT_HEADERS,
            body=None,
            preload_content=False,
            retries=MyService.MAX_REDIRECTS
        )

    def test_raw_query_success(self):
        method = SparqlMethod.GET
        endpoint = 'http://a.b/c'
        statement = 'Hello'
        http_status = 200
        http_body = 'We are not parsing this'

        mock_response = MagicMock(spec=HTTPResponse, name="Mock response")
        mock_response.status = http_status
        mock_response.read.return_value = http_body.encode()
        service = self.MyTestService(method)
        service.endpoint = endpoint
        service.pool_request = MagicMock(return_value=mock_response)

        result_set = Query(service).raw_query(statement)
        assert type(result_set) is RawResultSet
        assert result_set.get_raw_response_text() == http_body

        service.pool_request.assert_called_once_with(
            method,
            f'{endpoint}?query={statement}',
            headers=self.DEFAULT_HEADERS,
            body=None,
            preload_content=False,
            retries=MyService.MAX_REDIRECTS
        )

    def test_raw_query_exception(self):
        method = SparqlMethod.GET
        endpoint = 'http://a.b/c'
        statement = 'Hello'
        exception = ConnectTimeoutError()

        service = self.MyTestService(method)
        service.endpoint = endpoint
        service.pool_request = MagicMock(side_effect=exception)

        with pytest.raises(SparqlException) as exc_info:
            Query(service).raw_query(statement)

        assert exc_info.value.message.index('HTTP Error') == 0
        assert exc_info.value.__cause__ is exception
        service.pool_request.assert_called_once_with(
            method,
            f'{endpoint}?query={statement}',
            headers=self.DEFAULT_HEADERS,
            body=None,
            preload_content=False,
            retries=MyService.MAX_REDIRECTS
        )

    @staticmethod
    def set_prefixes(q: Query) -> Query:
        q.set_prefix('a', 'url/1')
        q.set_prefix('b', 'url/2')
        return q

    PREFIX_STRING_PLAIN = 'PREFIX a: <url/1> PREFIX b: <url/2>'
    PREFIX_STRING_ENCODED = 'PREFIX+a%3A+%3Curl%2F1%3E+PREFIX+b%3A+%3Curl%2F2%3E'

    @staticmethod
    def set_named_graphs(q: Query) -> Query:
        q.named_graphs.append('url/5')
        q.named_graphs.append('url/6')
        return q

    NAMED_GRAPH_URI_STRING = '&named-graph-uri=url%2F5&named-graph-uri=url%2F6'

    @staticmethod
    def set_default_graphs(q: Query) -> Query:
        q.default_graphs.append('url/3')
        q.default_graphs.append('url/4')
        return q

    DEFAULT_GRAPH_URI_STRING = 'default-graph-uri=url%2F3&default-graph-uri=url%2F4'

    STATEMENT_PLAIN = 'SELECT a FROM b;'
    STATEMENT_ENCODED = 'SELECT+a+FROM+b%3B'
    FULL_STATEMENT_ENCODED = PREFIX_STRING_ENCODED + '+' + STATEMENT_ENCODED
    GRAPH_URI_STRINGS = DEFAULT_GRAPH_URI_STRING + NAMED_GRAPH_URI_STRING
    FULL_STATEMENT_PLAIN = PREFIX_STRING_PLAIN + ' ' + STATEMENT_PLAIN
    FULL_STATEMENT_URI_ENCODED = f'query={FULL_STATEMENT_ENCODED}&{GRAPH_URI_STRINGS}'
    ONLY_STATEMENT_URI_ENCODED = 'query=' + STATEMENT_ENCODED

    URI_GET_FULL = MyService.ENDPOINT + '?' + FULL_STATEMENT_URI_ENCODED
    URI_GET_MINIMAL = MyService.ENDPOINT + '?' + ONLY_STATEMENT_URI_ENCODED
    URI_POST_FULL = MyService.ENDPOINT + '?' + GRAPH_URI_STRINGS
    URI_POST_MINIMAL = MyService.ENDPOINT

    TEST_QUERY_CONTENT_BODY = [
        [
            SparqlMethod.GET, False,
            URI_GET_MINIMAL,
            None,
            None,
        ],
        [
            SparqlMethod.GET, True,
            URI_GET_FULL,
            None,
            None,
        ],
        [
            SparqlMethod.POST, False,
            URI_POST_MINIMAL,
            Query.CONTENT_TYPE_POST,
            STATEMENT_PLAIN,
        ],
        [
            SparqlMethod.POST, True,
            URI_POST_FULL,
            Query.CONTENT_TYPE_POST,
            FULL_STATEMENT_PLAIN,
        ],
        [
            SparqlMethod.POST_URL_ENCODED, False,
            MyTestService.ENDPOINT,
            Query.CONTENT_TYPE_POST_URLENCODED,
            ONLY_STATEMENT_URI_ENCODED,
        ],
        [
            SparqlMethod.POST_URL_ENCODED, True,
            MyTestService.ENDPOINT,
            Query.CONTENT_TYPE_POST_URLENCODED,
            FULL_STATEMENT_URI_ENCODED,
        ],
    ]

    @pytest.mark.parametrize('method, full, exp_uri, exp_content_type, exp_body', TEST_QUERY_CONTENT_BODY)
    def test_uri_content_body(
            self,
            method: SparqlMethod,
            full: bool,
            exp_uri: str,
            exp_content_type: str | None,
            exp_body: str | None
    ):
        """
        This method tests summarily the results of query_uri(), content_type_header() and query_body(),
        all of which are used inside the query() method.
        :param method: HTTP method used
        :param full: Whether we are testing full (graphs, prefixes) or minimal (just a statement) case
        :param exp_uri: Expected URI string for the web request
                        (as returned by query_uri())
        :param exp_content_type: Expected request content type for the web request
                                 (as returned by content_type_header())
        :param exp_body: Expected request body content
                         (as returned by query_body())
        """
        q = Query(self.MyTestService(method))
        if full:
            self.set_prefixes(q)
            self.set_default_graphs(q)
            self.set_named_graphs(q)

        assert q.query_uri(self.STATEMENT_PLAIN) == exp_uri

        if exp_content_type is None:
            assert q.CONTENT_TYPE_HEADER not in q.content_type_header()
        else:
            assert q.content_type_header()[q.CONTENT_TYPE_HEADER] == exp_content_type

        if exp_body:
            assert q.query_body(self.STATEMENT_PLAIN) == exp_body.encode()
        else:
            assert q.query_body(self.STATEMENT_PLAIN) is None

    def test_query_uri_with_parameterised_endpoint_get(self):
        """
        Tests special query_uri case, where the endpoint already contains other parameters
        """
        q = Query(self.MyTestService(SparqlMethod.GET))
        param_endpoint = 'https://a.b.c/d?source=abcd'
        q.endpoint = param_endpoint
        self.set_prefixes(q)
        self.set_default_graphs(q)
        self.set_named_graphs(q)
        assert q.query_uri(self.STATEMENT_PLAIN) == param_endpoint + '&' + self.FULL_STATEMENT_URI_ENCODED

    def test_query_uri_with_parameterised_endpoint_post(self):
        """
        Tests special query_uri case, where the endpoint already contains other parameters
        """
        q = Query(self.MyTestService(SparqlMethod.POST))
        param_endpoint = 'https://a.b.c/d?source=abcd'
        q.endpoint = param_endpoint
        self.set_prefixes(q)
        self.set_default_graphs(q)
        self.set_named_graphs(q)
        assert q.query_uri(self.STATEMENT_PLAIN) == param_endpoint + '&' + self.GRAPH_URI_STRINGS

    def test_param_string(self):
        q = Query(self.MyTestService(SparqlMethod.POST_URL_ENCODED))  # Method is irrelevant
        self.set_named_graphs(q)
        self.set_default_graphs(q)
        self.set_prefixes(q)
        assert q.param_string(None) == self.GRAPH_URI_STRINGS
        assert q.param_string('') == self.GRAPH_URI_STRINGS
        assert q.param_string(self.STATEMENT_PLAIN) == self.FULL_STATEMENT_URI_ENCODED

    def test_param_string_minimal(self):
        q = Query(self.MyTestService(SparqlMethod.POST_URL_ENCODED))  # Method is irrelevant
        assert q.param_string(None) == ''
        assert q.param_string('') == ''
        assert q.param_string(self.STATEMENT_PLAIN) == self.ONLY_STATEMENT_URI_ENCODED

    def test_query_string(self):
        q = Query(self.MyTestService())
        self.set_prefixes(q)
        assert q.query_string(self.STATEMENT_PLAIN) == self.FULL_STATEMENT_PLAIN

    def test_query_string_no_prefix(self):
        q = Query(self.MyTestService())
        assert q.query_string(self.STATEMENT_PLAIN) == self.STATEMENT_PLAIN
