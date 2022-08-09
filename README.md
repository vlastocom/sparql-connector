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
s = sparqlc.Service(endpoint, "utf-8", "GET")
```

Then you make the query:

```python
result = s.query(statement)
```

If you have made a SELECT query, then you can read the result with `fetchone()` or `fetchall()`:

```python
for row in result.fetchone():
    pass # Do something useful here
```

If you have made an ASK query, then you can read the result (a boolean value) with `hasresult()`:

```python
works = result.hasresult()
```

## How it works

```python
>>> import sparqlc
>>> q = ('SELECT DISTINCT ?station, ?orbits WHERE { '
...      '?station a <http://dbpedia.org/ontology/SpaceStation> . '
...      '?station <http://dbpedia.org/property/orbits> ?orbits . '
...      'FILTER(?orbits > 50000) } ORDER BY DESC(?orbits)')
>>> ep = 'http://dbpedia.org/sparql'

>>> result = sparqlc.query(ep, q)
>>> result.variables
[u'station', u'orbits']

>>> for row in result:
...     print(f'{row[0]} - {row[1]} orbits')
'http://dbpedia.org/resource/Mir - 86331 orbits'
'http://dbpedia.org/resource/Salyut_7 - 51917 orbits'

>>> result = sparqlc.raw_query('http://dbpedia.org/sparql', q)
>>> result.variables
[u'station', u'orbits']

>>> for row in result:
...     print(f'row: {row}')
row: (<IRI <http://dbpedia.org/resource/Mir>>, <Literal "86331"^^<http://www.w3.org/2001/XMLSchema#int>>)
row: (<IRI <http://dbpedia.org/resource/Salyut_7>>, <Literal "51917"^^<http://www.w3.org/2001/XMLSchema#int>>)
```

## sparqlc module
The `sparqlc` module can be invoked in several different ways.
To quickly run a query, use `sparqlc.query()` or  `sparqlc.raw_query()`.
Results are encapsulated in a `ResultSet` or a `RawResultSet` instance,
difference being that the former instance contains values  converted to
plain Python types, whereas the `RawResultSet` contains the parsed `RDFTerm`
objects. `ResultSet.unpack_row()` method can be used to unpack those later.

```python
>>> result = sparqlc.query(endpoint, query)
>>> for row in result:
>>>    print(f'row: {row}')
row: ('http://dbpedia.org/resource/Mir', 86331)
row: ('http://dbpedia.org/resource/Salyut_7', 51917)
```

## Command line use

```
>>> sparql-connector.py [-i] endpoint
    -i Interactive mode
```

If interactive mode is enabled, the program reads queries from the console and then executes them. 
Use a double line (two ‘enters’) to separate queries.
Otherwise, the query is read from standard input.

## RDF wrapper classes

`sparqlc.RDFTerm`
:   Super class containing methods to override. `sparqlc.IRI`, `sparqlc.Literal` and `sparqlc.BlankNode` all inherit 
from `sparqlc.RDFTerm`.

`n3()`
:   Return a Notation3 representation of this term.

`class sparqlc.IRI(value)`
:   An RDF resource.

`class sparqlc.Literal(value, datatype=None, lang=None)`
:   Literals. These can take a data type or a language code.

`class sparqlc.BlankNode(value)`
:   Blank node. Similar to IRI but lacks a stable identifier.

`XSD_STRING, XSD_INT, XSD_LONG, XSD_DOUBLE, XSD_FLOAT, XSD_INTEGER, XSD_DECIMAL, XSD_DATETIME, XSD_DATE, XSD_TIME, XSD_BOOLEAN`
:   If required, use those strings for identifying the datatype of the RDF Literal instead of creating your own. 

## Query utilities

`class sparql.Service(endpoint, qs_encoding='utf-8')`
:   This is the main entry to the library. The user creates a Service, then sends a query to it. 
If we want to have persistent connections, then open them here.

`class sparqlc.RawResultSet(file_descriptor, encoding = 'utf-8')`
:   Represents the query result set, can be read using the following method. 
Each row of the raw result set is a collection of `RDFTerm` objects parsed from 
the response. The `RawResultSet` object can be used as an iterator.

`class sparqlc.ResultSet(fp)`
:   Extends `RawResultSet`, the difference is that each row contains 
converted values of the respective `RDFTerm` objects (see `unpack_row` below)

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

`sparqlc.ResultSet.hasresult()`
:   ASK queries are used to test if a query would have a result. If the query is an ASK query there won’t be 
an actual result, and fetchone() will return nothing. Instead, this method can be called to check the result from 
the ASK query. If the query is a SELECT statement, then the return value of `hasresult()` is `None`, 
as the XML result format doesn't tell you if there are any rows in the result until you have read the first one.

`sparql.parse_n3_term(src)`
:   Parse a Notation3 value into a RDFTerm object (IRI or Literal). This parser understands IRIs and quoted strings; 
basic non-string types (integers, decimals, booleans, etc) are not supported yet.

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
    - DATE, TIME and DATETIME are converted to date, time and datetime respectively, 
      but only if the python-dateutil library is found, then . For other conversions, 
      an extra argument convert may be passed. It should be a callable accepting 
      two arguments: the serialized value as a unicode object, and the XSD datatype.

`sparqlc.query(endpoint, query), sparqlc.raw_query(endpoint, query)`
:   Convenient method to execute a query. 
Exactly equivalent to `sparqlc.Service(endpoint).query(query)`
and `sparqlc.Service(endpoint).raw_query(query)`.
The `query()` methods return `ResultSet` with converted values,
the `raw_query()` methods return a `RawResultSet` containing unconverted
`RDFTerm` objects parsed from the SparQL response.
Use `RawResultSet.unpack_row()` to convert these later.

## Conversion of data types
The library will automatically convert typed literals to a corresponding
simple type in Python. Dates are also converted if the 
[dateutil](http://labix.org/python-dateutil) library is available.

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

**NB:** Integration tests depend on external public queries, which, as the world changes,
may occasionally become broken. If that occurs, please feel free to fix those
in a separate PR.


# License
The contents off this package are subject to the 
[Mozilla Public License Version 2.0](https://github.com/vlastocom/sparql2/blob/master/LICENSE).

Owner of this fork: Vlasto Chvojka

Original authors of SPARQL client code:
* Søren Roug, EEA
* Alex Morega, Eau de Web
