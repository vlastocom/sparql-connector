from unittest.mock import MagicMock

from urllib3 import HTTPResponse

# noinspection PyProtectedMember
from service_base import ServiceBase, SparqlMethod, USER_AGENT


class MyService(ServiceBase):
    ENDPOINT = 'http://a.b.com/d'
    ENCODING = 'utf-32'
    METHOD = SparqlMethod.POST
    ACCEPT = 'abcdefg'
    MAX_REDIRECTS = 123
    TIMEOUT = 5.54

    def __init__(self, timeout: float):
        super().__init__(
            MyService.METHOD,
            MyService.ENDPOINT,
            MyService.ENCODING,
            MyService.ACCEPT,
            MyService.MAX_REDIRECTS,
            timeout
        )

    def pool_request(self, method: SparqlMethod, url: str, **kwargs) -> HTTPResponse:
        return MagicMock(HTTPResponse)


class TestServiceMixin:

    def test_init(self):
        s = MyService(MyService.TIMEOUT)
        assert s.method is MyService.METHOD
        assert s.endpoint == MyService.ENDPOINT
        assert s.encoding == MyService.ENCODING
        assert s.headers == {
            'Accept': MyService.ACCEPT,
            'User-Agent': USER_AGENT,
        }
        assert s.accept == MyService.ACCEPT
        assert s.default_graphs == []
        assert s.named_graphs == []
        assert s.prefixes == dict()
        assert s.max_redirects == MyService.MAX_REDIRECTS
        assert s.timeout == MyService.TIMEOUT
        assert s.request_kwargs == {
            MyService.PARAM_TIMEOUT: MyService.TIMEOUT,
            MyService.PARAM_MAX_REDIRECTS: MyService.MAX_REDIRECTS,
        }

    def test_accept(self):
        s = MyService(MyService.TIMEOUT)
        assert s.accept == MyService.ACCEPT
        assert s.headers == {
            'Accept': MyService.ACCEPT,
            'User-Agent': USER_AGENT,
        }

        new_accept = 'SOME_OTHER_MIME'
        s.accept = new_accept
        assert s.accept == new_accept
        assert s.headers == {
            'Accept': new_accept,
            'User-Agent': USER_AGENT,
        }

    def test_timeout_zero(self):
        s = MyService(0.0)
        assert s.timeout == 0.0
        assert s.request_kwargs == {
            MyService.PARAM_MAX_REDIRECTS: MyService.MAX_REDIRECTS,
        }

    def test_timeout_delete(self):
        s = MyService(MyService.TIMEOUT)
        s.timeout = 0.0
        assert s.timeout == 0.0
        assert s.request_kwargs == {
            MyService.PARAM_MAX_REDIRECTS: MyService.MAX_REDIRECTS,
        }
