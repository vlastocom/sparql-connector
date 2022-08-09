#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The contents of this file are subject to the Mozilla Public
# License Version 1.1 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of
# the License at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS
# IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
# implied. See the License for the specific language governing
# rights and limitations under the License.
#
# The Original Code is "SPARQL Client"
#
# The Initial Owner of the Original Code is European Environment
# Agency (EEA).  Portions created by Eau de Web are
# Copyright (C) 2011 by European Environment Agency.  All
# Rights Reserved.
#
# Contributor(s):
#  Søren Roug, EEA
#  Alex Morega, Eau de Web
#  David Bătrânu, Eau de Web
#  Vlastimil Chvojka

# noinspection PyShadowingNames,PyUnresolvedReferences
"""
The `sparql-connect` module can be invoked in several different ways.
To quickly run a query use :func:`query`. Results are encapsulated in a
:class:`_ResultsParser` instance::

    >>> result = sparql.query(endpoint, query)
    >>> for row in result:
    >>>    print(row)


Command-line use
----------------

::

    sparql.py [-i] endpoint
        -i Interactive mode

If interactive mode is enabled, the program reads queries from the console
and then executes them. Use a double line (two 'enters') to separate queries.

Otherwise, the query is read from standard input.
"""

import sys
from typing import List, Tuple

from .exception import SparqlException
from .service import query
from .version import VERSION


def parse_command_line() -> Tuple[str, bool]:
    """
    Parses command line arguments, errors and exists in the case of failure
    :return: Endpoint and a flag indicating if this tool should be run in an
             interactive mode
    """
    from optparse import OptionParser

    parser = OptionParser(usage="%prog [-i] endpoint",
                          version="%prog " + str(VERSION))
    parser.add_option("-i", dest="interactive", action="store_true",
                      help="Enables interactive mode")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("Endpoint must be specified")
    return args[0], options.interactive


def read_lines() -> List[str]:
    lines = []
    while True:
        next_line = input()
        if not next_line:
            return lines
        else:
            lines.append(next_line)


def _run_interactive(endpoint: str) -> None:
    while True:
        try:
            lines = read_lines()
            if lines:
                sys.stdout.write("Querying...")
                result = query(endpoint, " ".join(lines))
                sys.stdout.write("  done\n")
                for row in result:
                    print("\t".join(row))
        except SparqlException as e:
            print(e.message)


def _run_batch(endpoint: str) -> None:
    q = sys.stdin.read()
    try:
        result = query(endpoint, q)
        for row in result:
            print("\t".join(row))
    except SparqlException as e:
        print(e.message)


def _run() -> None:
    import sys
    import codecs

    try:
        c = codecs.getwriter(sys.stdout.encoding)
    except LookupError:
        c = codecs.getwriter('ascii')
    sys.stdout = c(sys.stdout, 'replace')

    ep, interactive = parse_command_line()
    if interactive:
        _run_interactive(ep)
    else:
        _run_batch(ep)


if __name__ == '__main__':
    _run()
