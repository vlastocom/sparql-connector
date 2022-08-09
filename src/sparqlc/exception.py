class SparqlException(Exception):
    """ Sparql generic exception """
    def __init__(self, message: str):
        self.message = message


class SparqlProtocolException(SparqlException):
    """ Sparql HTTP related exception """
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code: int = code


class SparqlParseException(SparqlException):
    """ Sparql exception related to parsing the content of the response """
    def __init__(self, message: str, data: str):
        super().__init__(message)
        self.data = data
