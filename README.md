# sparql2 - A new SPARQL HTTP client library
SPAQL query library for SELECT and ASK queries against a SPARQL endpoint via HTTP.

This code (and README) is using an earlier [eea/sparql-client](https://github.com/eea/sparql-client), 
which stopped being maintained and kept supporting old versions of Python. This package drops that support
and makes it easier to be maintained against the new Python versions.

The code will automatically convert literals to corresponding Python  types.

API is based on 
[SPARQL_JavaScript_Library](https://web.archive.org/web/20120518014957/http://www.thefigtrees.net/lee/sw/sparql.js) 
by Lee Feigenbaum and Elias Torres. Heavy influence from Juan Manuel Caicedo’s SPARQL library.

## API

First you open a connection to the endpoint:

```python
s = sparql.Service(endpoint, "utf-8", "GET")
```

Then you make the query:

```python
result = s.query(statement)
```

If you have made a SELECT query, then you can read the result with `fetchone()` or `fetchall()`:

```python
for row in result.fetchone():
```

If you have made an ASK query, then you can read the result (a boolean value) with `hasresult()`:

```python
works = result.hasresult()
```

## How it works

```python
>>> import sparql
>>> q = ('SELECT DISTINCT ?station, ?orbits WHERE { '
...      '?station a <http://dbpedia.org/ontology/SpaceStation> . '
...      '?station <http://dbpedia.org/property/orbits> ?orbits . '
...      'FILTER(?orbits > 50000) } ORDER BY DESC(?orbits)')
>>> result = sparql.query('http://dbpedia.org/sparql', q)
>>> result.variables
[u'station', u'orbits']

>>> for row in result:
...     print 'row:', row
...     values = sparql.unpack_row(row)
...     print values[0], "-", values[1], "orbits"
row: (<IRI <http://dbpedia.org/resource/Mir>>, <Literal "86331"^^<http://www.w3.org/2001/XMLSchema#int>>)
http://dbpedia.org/resource/Mir - 86331 orbits
row: (<IRI <http://dbpedia.org/resource/Salyut_7>>, <Literal "51917"^^<http://www.w3.org/2001/XMLSchema#int>>)
http://dbpedia.org/resource/Salyut_7 - 51917 orbits
```

## sparql module
The `sparql` module can be invoked in several different ways. 
To quickly run a query use `query()`. 
Results are encapsulated in a `_ResultsParser` instance:

```python
>>> result = sparql.query(endpoint, query)
>>> for row in result:
>>>    print row
```

## Command line use

```
>>> sparql.py [-i] endpoint
    -i Interactive mode
```

If interactive mode is enabled, the program reads queries from the console and then executes them. 
Use a double line (two ‘enters’) to separate queries.
Otherwise, the query is read from standard input.

## RDF wrapper classes

`sparql.RDFTerm`
:   Super class containing methods to override. `sparql.IRI`, `sparql.Literal` and `sparql.BlankNode` all inherit 
from `sparql.RDFTerm`.

`n3()`
:   Return a Notation3 representation of this term.

`class sparql.IRI(value)`
:   An RDF resource.

`class sparql.Literal(value, datatype=None, lang=None)`
:   Literals. These can take a data type or a language code.

`class sparql.BlankNode(value)`
:   Blank node. Similar to IRI but lacks a stable identifier.

## Query utilities

`class sparql.Service(endpoint, qs_encoding='utf-8')`
:   This is the main entry to the library. The user creates a Service, then sends a query to it. 
If we want to have persistent connections, then open them here.

`class sparql._ResultsParser(fp)`
:   Parse the XML result.

`__iter__()`
:   Synonym for fetchone().

`fetchall()`
:   Loop through the result to build up a list of all rows. Patterned after DB-API 2.0.

`fetchone()`
:   Fetches the next set of rows of a query result, returning a list. An empty list is returned when no more rows 
are available. If the query was an ASK request, then an empty list is returned as there are no rows available.

`hasresult()`
:   ASK queries are used to test if a query would have a result. If the query is an ASK query there won’t be 
an actual result, and fetchone() will return nothing. Instead, this method can be called to check the result from 
the ASK query. If the query is a SELECT statement, then the return value of `hasresult()` is `None`, 
as the XML result format doesn't tell you if there are any rows in the result until you have read the first one.

`sparql.parse_n3_term(src)`
:   Parse a Notation3 value into a RDFTerm object (IRI or Literal). This parser understands IRIs and quoted strings; 
basic non-string types (integers, decimals, booleans, etc) are not supported yet.

`sparql.unpack_row(row, convert=None, convert_type={})`
:   Convert values in the given row from RDFTerm objects to plain Python values: IRI is converted to a unicode string
containing the IRI value; BlankNode is converted to a unicode string with the BNode’s identifier, and Literal 
is converted based on its XSD datatype. The library knows about common XSD types (STRING becomes unicode, 
INTEGER and LONG become int, DOUBLE and FLOAT become float, DECIMAL becomes Decimal, BOOLEAN becomes bool).
If the python-dateutil library is found, then DATE, TIME and DATETIME are converted to date, time and datetime 
respectively. For other conversions, an extra argument convert may be passed. It should be a callable accepting 
two arguments: the serialized value as a unicode object, and the XSD datatype.

`sparql.query(endpoint, query)`
:   Convenient method to execute a query. Exactly equivalent to `sparql.Service(endpoint).query(query)`

## Conversion of data types
The library will automatically convert typed literals to a corresponding
simple type in Python. Dates are also converted if the [dateutil](http://labix.org/python-dateutil) library is
available.

# Contributing to the project
TBD

# License
The contents off this package are subject to the 
[Mozilla Public License Version 2.0](https://github.com/vlastocom/sparql2/blob/master/LICENSE).

Owner of this project: Vlasto Chvojka

Original authors of SPARQL client:
* Søren Roug, EEA
* Alex Morega, Eau de Web
