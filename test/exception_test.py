from sparqlc import SparqlException, SparqlParseException, SparqlProtocolException


class TestSparqlException:
    def test_init(self):
        exc = SparqlException('message from me')
        assert exc.message == 'message from me'
        assert isinstance(exc, Exception)


class TestSparqlProtocolException:
    def test_init(self):
        exc = SparqlProtocolException(123, 'message from me')
        assert exc.code == 123
        assert exc.message == 'message from me'
        assert isinstance(exc, SparqlException)


class TestSparqlParseException:
    def test_init(self):
        exc = SparqlParseException('message from me', 'some bloody data')
        assert exc.message == 'message from me'
        assert exc.data == 'some bloody data'
        assert isinstance(exc, SparqlException)
