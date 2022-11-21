# sparql-connector - A SPARQL HTTP client library
SPAQL query library for SELECT and ASK queries against a SPARQL endpoint via HTTP.

This code (and README) is building upon an earlier
[eea/sparql-client](https://github.com/eea/sparql-client),
which stopped being maintained in 2020 and the old code got very complicated,
as it kept supporting old versions of Python. This package drops that support
and makes it easier to be maintained against the new Python versions.

The code will automatically convert literals to corresponding Python types.

API is based on
[SPARQL_JavaScript_Library](https://web.archive.org/web/20120518014957/http://www.thefigtrees.net/lee/sw/sparql.js)
by Lee Feigenbaum and Elias Torres. Heavy influence from Juan Manuel
Caicedo’s SPARQL library.

## API

First you open a connection to the endpoint:

```python
import sparqlc
endpoint = 'http://a.b/c'
svc = sparqlc.Service(endpoint)
```

Then you make the query:

```python
statement = 'SELECT ... ORDER BY ...'
results = svc.query(statement)
```

If you have made a SELECT query, then you can read the result using iterator:

```python
for row in results:
    pass # Do something useful here
```

Alternatively, you can read all rows at once (small queries only):

```python
rows = results.fetch_rows(limit=1000)
for row in rows:
    pass # Do something useful here
```

If you have made an ASK query, then you can read the result (a boolean value) with `hasresult()`:

```python
works = result.hasresult()
```

## How it works

```python
>>> import sparqlc
>>> q = 'SELECT DISTINCT ?station, ?orbits WHERE { ' \
...      '?station a <http://dbpedia.org/ontology/SpaceStation> . ' \
...      '?station <http://dbpedia.org/property/orbits> ?orbits . ' \
...      'FILTER(?orbits > 50000) } ORDER BY DESC(?orbits)'
>>> ep = 'http://dbpedia.org/sparql'

>>> sparqlc.query(ep, q, sparqlc.SparqlMethod.GET)
>>> result.variables
[u'station', u'orbits']

>>> for row in result:
...     print(f'{row[0]} - {row[1]} orbits')
'http://dbpedia.org/resource/International_Space_Station - 133312 orbits'
'http://dbpedia.org/resource/Mir - 86331 orbits'
'http://dbpedia.org/resource/Salyut_7 - 51917 orbits'
'http://dbpedia.org/resource/Kosmos_557 - ~175 orbits'


>>> result = sparqlc.raw_query(ep, q, sparqlc.SparqlMethod.GET)
>>> result.variables
[u'station', u'orbits']

>>> for row in result:
...     print(f'row: {row}')
row: (<IRI <http://dbpedia.org/resource/International_Space_Station>>, <Literal "133312"^^<http://www.w3.org/2001/XMLSchema#integer>>)
row: (<IRI <http://dbpedia.org/resource/Mir>>, <Literal "86331"^^<http://www.w3.org/2001/XMLSchema#integer>>)
row: (<IRI <http://dbpedia.org/resource/Salyut_7>>, <Literal "51917"^^<http://www.w3.org/2001/XMLSchema#integer>>)
row: (<IRI <http://dbpedia.org/resource/Kosmos_557>>, <Literal "~175"@en>)
```

## Programmatic use
As demonstrated in the above example, the `sparqlc` module can be invoked in several different ways:

* To quickly run a query, use `sparqlc.query()` or  `sparqlc.raw_query()`.
Results are encapsulated in a `ResultSet` or a `RawResultSet` instance respectively.
The only difference is that the former instance contains values converted to
primitive Python types, whereas the `RawResultSet` contains the parsed `RDFTerm`
objects. Use `ResultSet.unpack_row()` method to unpack those later.
* It is also possible to construct a `sparqlc.Service` object
(vaguely representing endpoint and its parameters) and then construct
and execute `Query` objects using their `query()` or `query_raw()` methods.

### Operations
This library supports only query operation, i.e. ASK and SELECT queries of the SparQL standard.
Update operation is not supported.

### Protocol methods
All three standard HTTP protocol methods are supported, the correct option can be selected
by using the correct `sparqlc.SparqlMethod` enum value:
* [GET](https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-via-get) - `sparqlc.SparqlMethod.GET`
* [Direct POST](https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-via-post-direct) - `sparqlc.SparqlMethod.POST`
* [POST with URL-encoded parameters](https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#update-via-post-urlencoded) - `sparqlc.SparqlMethod.POST_URL_ENCODED`

**Note:** Not all endpoints support all three SparQL methods.
For example, the above code snippet queries an online resource, [DBpedia](https://www.dbpedia.org/).
DBpedia only supports GET method.
Using any other method will result in a `SparqlProtocolException`,
with the underlying course being HTTP response code "406 - Not Acceptable".

## Command line use

```
>>> sparql-connector.py [-i] endpoint
    -i Interactive mode
```

If interactive mode is enabled, the program reads queries from the console and then executes them. 
Use a double line (two ‘enters’) to separate queries.
Otherwise, the query is read from standard input.

## Service

`sparqlc.query(endpoint, query), sparqlc.raw_query(endpoint, query)`
:   A convenient method to execute a query.
Exactly equivalent to `sparqlc.Service(endpoint).query(query)`
and `sparqlc.Service(endpoint).raw_query(query)`.
The `query()` methods return `ResultSet` with converted values,
the `raw_query()` methods return a `RawResultSet` containing unconverted
`RDFTerm` objects parsed from the SparQL response.
Use `RawResultSet.unpack_row()` to convert these later.


`class sparql.Service(endpoint, method, encoding, accept, max_redirects, timeout)`
:   This object represents the service endpoint on which the queries can be executed.
Creates a Service instance, then create a query object using `Sevice.create_query()`
and execute it using `Query.query()` or `Query.raw_query()` methods.
Service is defined by the endpoint URL, HTTP method, encoding (utf-8 being the golden
default). You can also define other parameters which will be default for all queries
on this endpoint, for example add / replace custom headers, set the maximum allowed
number of redirects and the duration of the request timeout. The expected format
of the response (XML, JSON, CSV) can be changed setting the parameter `accept`
to one of the `RESULT_TYPE_*` values (see below). It is also possible to  at this level.


The following properties are common for `Service` and `Query` (see below) objects:
* `method: sparqlc.SparqlMethod` - The HTTP method used for the queries. Default: POST
* `endpoint: str` - The URL of the SPARQL endpoint
* `encoding: str` - The encoding used for the request and expected on the response. Default: utf-8
* `accept: str` - Defines the expected type of response. Pre-defined constants `RESULT_TYPE_*`
  (see below) are provided for the three standard result types. Default: XML
* `default_graphs: List[str]` - The list of
  [default graphs](https://www.w3.org/TR/sparql11-query/#namedAndDefaultGraph),
  passed to the endpoint together with the query as per Sparql protocol. Default: empty
* `named_graphs: List[str]` - The list of
  [named graphs](https://www.w3.org/TR/sparql11-query/#namedAndDefaultGraph),
  passed to the endpoint together with the query as per Sparql protocol. Default: empty
* `prefixes: Dict[str, str]` - the map of prefixes used in queries. The query will be prepended
  all the prefixes in this map ("PREFIX name: <uri>"). Use `set_prefix()` method
  to set a specific prefix. Default: empty
* `max_redirects: int` - maximum number of redirects the query allows before an error is reported.
   Default: 5
* `timeout: float` - maximum number of time allowed for the connection open. Default: 0.0 (infinite)
* `request_kwargs: Disct[str, Any]` - Only for experts. This is the set of name-value parameters,
  which will be combined with many of the above and passed as `**kwargs`
  of the `urllib3.PoolManager.request` call. If you know what you are doing can use this to modify
  the HTTP request behaviour further.

`RESULT_TYPE_SPARQL_XML`, `RESULT_TYPE_SPARQL_JSON`, `RESULT_TYPE_XML_SCHEMA`
: Parameters, which can be used in the constructor of the `Service` or `Query` objects
to determine the result set (XML, JSON, XML Schema, respectively).
Please note that the ResultSet can only parse XML result type. If you want to
access a JSON response, for example, you have to use `ResultSet.get_raw_response()`
to read the actual raw response body and parse it yourself.

`sparql.Service.create_query()`
: Creates a query for the service. All the attributes set on the `Service` object
will be automatically copied as defaults for the query (it is possible to subsequently
modify them).

`sparql.Service.authenticate(username, password)`
: Enables insertion of a simple authentication header.
Only Basic Authentication is supported.
Make sure you call this method **before** creating query objects.

## Query object

`class sparqlc.Query`
: A basic query object. Construct this object by calling `Service.create_query()`
  on the service instance. All of the above mentioned properties common to `Service`
  and `Query` will be copied to this new object. They can be then further modified.

`sparqlc.Query.query(statement)`
: Execute the SPARQL statement on the endpoint. Returns `ResultSet`, containing
  the response data, conveniently converted to the native Python types (see below
  on type conversions).

`sparqlc.Query.raw_query(statement)`
: Execute the SPARQL statement on the endpoint. Returns `RawResultSet`, containing
  the response data using RDF type objects described in "RDF type wrapper classes"
  section.

## Working with results

Query results come in 2 forms, the difference is the conversion state of objects:


`class sparqlc.RawResultSet(file_descriptor, encoding = 'utf-8')`
:   Represents the query result set, can be read using the following method. 
    Each row of the raw result set is a collection of `RDFTerm` objects parsed from
    the response.

`class sparqlc.ResultSet(file_descriptor, encoding = 'utf-8')`
:   Extends `RawResultSet`, the difference is that each row contains 
converted values of the respective `RDFTerm` objects (see `unpack_row` below)

### ASK queries
Ask queries return a simple boolean answer indicating whether the query
would return data or not:

```python
import sparqlc
query = 'ASK ... '
result = sparqlc.raw_query(query).has_result()
```

`sparqlc.ResultSet.hasresult()`
:   ASK queries are used to test if a query would have a result. If the query is an ASK query there won’t be
an actual result, and `fetch_next()` will return nothing. Instead, this method can be called to check the result from
the ASK query. If the query is a SELECT statement, then the return value of `hasresult()` is `None`,
as the XML result format doesn't tell you if there are any rows in the result until you have read the first one.


### SELECT: Fetching all rows at once

For small expected result sets, it is possible to quickly fetch all rows:

```python
import sparqlc
query = 'SELECT ... ORDER BY ...'
results = sparqlc.raw_query(query).fetch_rows(limit=100)
for row in results:
    print(row)
```

The default limit is 0, which means that the whole data set will be fetched.
This only works for small data sets. For large data sets, iterating through
the results is recommended.

### SELECT: Iterating through result sets

Both result set objects can be used as an iterator, e.g. in a `for` loop:

```python
import sparqlc
query = 'SELECT ... ORDER BY ...'
results = sparqlc.raw_query(query)
for row in results:
    print(row)
```

`sparqlc.ResultSet.__iter__()`
:   Synonym for `fetch_next()`. 
Enables `RawResultSet` and `ResultSet` to be iterated in the `for ...` loop. 

`sparqlc.ResultSet.fetch_rows()`
:   Fetches the list of all rows returned by the query.

`sparqlc.ResultSet.fetch_next()`
:   Fetches the next row of a query result, returning the tuple of 
`RDFTerm` objects (`RawResultSets`) or their values (`ResultSet`). 
None is returned when no more rows are available. 
If the query was an ASK request, None is returned as there are 
no rows available.


### Open / close status
Result set is constructed on a file descriptor, which could be a file
in a file system, but if returned from `query()` or `raw_query()` method,
it is based on an open byte stream over the TCP connection to the SPARQL endpoint.
The `closed` property indicates if the underlying stream is still open.
Due to buffering inside the parser, the stream may actually close before
all results are parsed, that is expected behaviour.

On the other hand, to ensure each connection gets closed promptly in the case of exception,
for example in high query frequency situations, it is possible to use
the `ResultSet` in a `with` block:

```python
with sparqlc.raw_query(query) as results:
    for row in results:
        print(row)
```

### Accessing raw response
This library can parse only XML responses. It is, however, possible to receive
a JSON response by modifying `accept` parameter of the `Query` object.
In this case however, the response has to be parsed by the user:

```python
import sparqlc
endpoint = 'http://a.b/c'
statement = 'SELECT ... ORDER BY ...'
query = sparqlc.Service(endpoint, accept=sparqlc.RESULT_TYPE_SPARQL_JSON).create_query()
json_to_parse = query.query(statement).get_raw_response_text()
```

Please note once the `get_raw response_text()` is called, the parsing
the results the usual way will no longer work:

```python
import sparqlc
endpoint = 'http://a.b/c'
statement = 'SELECT ... ORDER BY ...'
query = sparqlc.Service(endpoint).create_query()
result = query.query(statement)
raw_xml_string = query.query(statement).get_raw_response_text()    # Will work
all_rows = result.fetch_rows()                                     # Will no longer work
```


### Converting the result values

`RawResultSet` returns the results in rows of rich `RDFTerm` objects parsed from the SPARQL XML response.
This may be useful in the situations where further manipulation of the rich types is required.

To convert these rows to the rows of primitive values, you can use `sparqlc.ResultSet.unpack_row`:

```python
import sparqlc
query = 'SELECT ... ORDER BY ...'
results = sparqlc.raw_query(query).fetch_rows(limit=100)
for row in results:
    print(row)
    converted_values = sparqlc.ResultSet.unpack_row(row)
    print(converted_values)
```

`sparqlc.ResultSet.unpack_row(row, convert=None, convert_type={})`
:   Converts values in the given row from `RDFTerm` objects to plain Python 
values: 

* IRI is converted to a unicode string containing the IRI value
* BlankNode is converted to a unicode string with the BNode’s identifier
* Literal is converted based on its XSD datatype. The library knows about common XSD types:
    - STRING becomes str
    - INTEGER and LONG become int
    - DOUBLE and FLOAT become float
    - DECIMAL becomes Decimal
    - BOOLEAN becomes bool
    - DATE, TIME and DATETIME are converted to date, time and datetime respectively.
    - For other conversions, an extra argument `convert` may be passed. It should be
      a callable accepting two arguments: the serialized value as a unicode object
      and the XSD datatype.
    - For trivial situations, for example where a custom literal type needs to be
      converted to a primitive Python type, you can specify these extra conversions
      by supplying the dictionary in `additional_types` argument:

```python
import sparqlc
query = 'SELECT ... ORDER BY ...'
results = sparqlc.raw_query(query).fetch_rows(limit=100)
my_types = {'http://www.my.org/MyFunkyDataType', int}
for row in results:
    print(row)
    converted_values = sparqlc.ResultSet.unpack_row(row, additional_types=my_types)
    print(converted_values)
```


## RDF type wrapper classes

The following classes represent the type system of values returned
by `RawResultSet.fetch_rows()` and `RawResultSet.fetch_one()`:

`class sparqlc.RDFTerm`
:   Super class containing methods to override. `sparqlc.IRI`, `sparqlc.Literal`
    and `sparqlc.BlankNode` all inherit
    from `sparqlc.RDFTerm`.

`sparqlc.RDFTerm.n3()`
:   Return a Notation3 representation of this term. `sparqlc.parse_n3_term()`
    provides the reverse of this operation, but only for `IRI` and some `Literal` instances.

`class sparqlc.IRI(value)`
:   An RDF resource.

`class sparqlc.Literal(value, datatype=None, lang=None)`
:   Literals. These can take a data type or a language code.

`class sparqlc.BlankNode(value)`
:   Blank node. Similar to IRI but lacks a stable identifier.

`XSD_STRING, XSD_INT, XSD_LONG, XSD_DOUBLE, XSD_FLOAT, XSD_INTEGER, XSD_DECIMAL, XSD_DATETIME, XSD_DATE, XSD_TIME, XSD_BOOLEAN`
:   If required, use those strings for identifying the datatype of the RDF Literal instead of creating your own.

`sparqlc.parse_n3_term(src)`
:   Parse a Notation3 value into a RDFTerm object (IRI or Literal). This parser understands IRIs and quoted strings;
basic non-string types (integers, decimals, booleans, etc) are not supported yet.

# Contributing to the project
## Setup
1. Fork the project into your private space and clone it to your machine
2. Install all supported versions of python interpreter
3. Create and activate the environment
    ```
    python venv venv
    . ./venv/bin/activate
    pip install -r requirements.build.txt
    ```
4. Run the unit tests in all possible python versions.
    ```
    tox
    ```

**NB:** Integration tests depend on external public endpoints, which, as the world changes,
may occasionally become broken. If that occurs, please feel free to fix those
in a separate PR.


# License
The contents off this package are subject to the 
[Mozilla Public License Version 2.0](https://github.com/vlastocom/sparql2/blob/master/LICENSE).

Owner of this fork: Vlasto Chvojka

Original authors of SPARQL client code:
* Søren Roug, EEA
* Alex Morega, Eau de Web
