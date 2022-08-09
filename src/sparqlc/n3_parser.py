import ast as ast_compiler
import re
from typing import cast

from .datatypes import IRI, Literal, RDFTerm

_n3parser_lang = re.compile(r'@(?P<lang>\w+)$')
_n3parser_datatype = re.compile(r'\^\^<(?P<datatype>[^\^"\'>]+)>$')


def parse_n3_term(src: str) -> RDFTerm:
    """
    Parse a Notation3 value into a RDFTerm object (IRI or Literal).

    This parser understands IRIs and quoted strings; basic non-string types
    (integers, decimals, booleans, etc) are not supported yet.
    """
    if src.startswith('<'):
        # `src` is an IRI
        if not src.endswith('>'):
            raise ValueError
        value = src[1:-1]
        if '<' in value or '>' in value:
            raise ValueError
        return IRI(value)
    else:
        datatype_match = _n3parser_datatype.search(src)
        if datatype_match is not None:
            datatype = datatype_match.group('datatype')
            src = _n3parser_datatype.sub('', src)
        else:
            datatype = None

        lang_match = _n3parser_lang.search(src)
        if lang_match is not None:
            lang = lang_match.group('lang')
            src = _n3parser_lang.sub('', src)
        else:
            lang = None

        # Python literals syntax is mostly compatible with N3.
        # We don't execute the code, just turn it into an AST.
        try:
            # should be fixed due to #111217
            ast = ast_compiler.parse("value = " + src)
        except Exception as exc:
            raise ValueError from exc

        if len(ast.body) != 1 or not isinstance(ast.body[0], ast_compiler.Assign):
            raise ValueError
        assign_node = cast(ast_compiler.Assign, ast.body[0])
        if not isinstance(assign_node.value, ast_compiler.Constant):
            raise ValueError
        value = cast(ast_compiler.Constant, assign_node.value).value

        if type(value) is not str:
            raise ValueError

        return Literal(value, datatype, lang)
