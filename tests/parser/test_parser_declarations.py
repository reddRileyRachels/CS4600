"""Unit tests for parse_type() and parse_declaration() (spec section 3).

Tokens are built by hand because the lexer is not merged yet. Once it is,
these can switch to tokenize("int x = 5;").
"""

import pytest

from src.lexer.token import Token, TokenKind as K
from src.parser.parser import Parser, ParseError
from src.ast.ast_node import DeclarationStmt, LiteralExpr, VariableExpr, UnaryExpr
from src.semantic.type import IntType, FloatType, MatrixType


def tokens(*pairs, line=1):
    """Build a token list from (kind, lexeme) pairs, ending with EOF."""
    result = [Token(kind, lexeme, line) for kind, lexeme in pairs]
    result.append(Token(K.EOF, "", line))
    return result


# --- parse_type -----------------------------------------------------------

def test_type_int():
    assert isinstance(Parser(tokens((K.INT, "int"))).parse_type(), IntType)


def test_type_float():
    assert isinstance(Parser(tokens((K.FLOAT, "float"))).parse_type(), FloatType)


def test_type_matrix_dimensions():
    t = Parser(tokens(
        (K.MATRIX, "matrix"), (K.LESSTHAN, "<"), (K.INTLIT, "2"),
        (K.COMMA, ","), (K.INTLIT, "3"), (K.GREATERTHAN, ">"),
    )).parse_type()
    assert isinstance(t, MatrixType)
    assert (t.rows, t.cols) == (2, 3)


def test_type_matrix_missing_comma_is_error():
    p = Parser(tokens(
        (K.MATRIX, "matrix"), (K.LESSTHAN, "<"), (K.INTLIT, "2"),
        (K.INTLIT, "3"), (K.GREATERTHAN, ">"),
    ))
    with pytest.raises(ParseError):
        p.parse_type()


def test_type_matrix_float_dimension_is_error():
    p = Parser(tokens(
        (K.MATRIX, "matrix"), (K.LESSTHAN, "<"), (K.FLOATLIT, "2.0"),
        (K.COMMA, ","), (K.INTLIT, "3"), (K.GREATERTHAN, ">"),
    ))
    with pytest.raises(ParseError):
        p.parse_type()


def test_type_matrix_zero_dimension_parses():
    # matrix<0,1> is syntactically fine; dims >= 1 is a semantic rule (spec 4.1)
    t = Parser(tokens(
        (K.MATRIX, "matrix"), (K.LESSTHAN, "<"), (K.INTLIT, "0"),
        (K.COMMA, ","), (K.INTLIT, "1"), (K.GREATERTHAN, ">"),
    )).parse_type()
    assert (t.rows, t.cols) == (0, 1)


def test_type_not_a_type_is_error():
    with pytest.raises(ParseError):
        Parser(tokens((K.IDENTIFIERLIT, "x"))).parse_type()


# --- parse_declaration ----------------------------------------------------

def test_declaration_without_initializer():
    # int x;
    d = Parser(tokens((K.INT, "int"), (K.IDENTIFIERLIT, "x"), (K.SEMICOLON, ";"))).parse_declaration()
    assert isinstance(d, DeclarationStmt)
    assert isinstance(d.declared_type, IntType)
    assert d.declared_identifier == "x"
    assert d.initializer is None


def test_declaration_with_int_initializer():
    # int x = 5;
    d = Parser(tokens(
        (K.INT, "int"), (K.IDENTIFIERLIT, "x"), (K.ASSIGNMENT, "="),
        (K.INTLIT, "5"), (K.SEMICOLON, ";"),
    )).parse_declaration()
    assert isinstance(d.initializer, LiteralExpr)
    assert d.initializer.value == 5


def test_declaration_float_with_variable_initializer():
    # float y = x;
    d = Parser(tokens(
        (K.FLOAT, "float"), (K.IDENTIFIERLIT, "y"), (K.ASSIGNMENT, "="),
        (K.IDENTIFIERLIT, "x"), (K.SEMICOLON, ";"),
    )).parse_declaration()
    assert isinstance(d.declared_type, FloatType)
    assert isinstance(d.initializer, VariableExpr)
    assert d.initializer.identifier == "x"


def test_declaration_negative_literal():
    # float b = -3;   (spec 4.3 example)
    d = Parser(tokens(
        (K.FLOAT, "float"), (K.IDENTIFIERLIT, "b"), (K.ASSIGNMENT, "="),
        (K.DIFFERENCE, "-"), (K.INTLIT, "3"), (K.SEMICOLON, ";"),
    )).parse_declaration()
    assert isinstance(d.initializer, UnaryExpr)
    assert d.initializer.operator == "-"
    assert d.initializer.operand.value == 3


def test_declaration_matrix_without_initializer():
    # matrix<2,3> A;
    d = Parser(tokens(
        (K.MATRIX, "matrix"), (K.LESSTHAN, "<"), (K.INTLIT, "2"), (K.COMMA, ","),
        (K.INTLIT, "3"), (K.GREATERTHAN, ">"), (K.IDENTIFIERLIT, "A"), (K.SEMICOLON, ";"),
    )).parse_declaration()
    assert (d.declared_type.rows, d.declared_type.cols) == (2, 3)
    assert d.declared_identifier == "A"


def test_declaration_records_line():
    toks = [Token(K.INT, "int", 4), Token(K.IDENTIFIERLIT, "x", 4),
            Token(K.SEMICOLON, ";", 4), Token(K.EOF, "", 4)]
    assert Parser(toks).parse_declaration().line == 4


def test_declaration_consumes_exactly_its_tokens():
    p = Parser(tokens((K.INT, "int"), (K.IDENTIFIERLIT, "x"), (K.SEMICOLON, ";")))
    p.parse_declaration()
    assert p.is_at_end()


# --- syntax errors (spec section 7) ----------------------------------------

def test_missing_initializer_is_error():
    # int x = ;   (spec section 7 example)
    p = Parser(tokens((K.INT, "int"), (K.IDENTIFIERLIT, "x"), (K.ASSIGNMENT, "="), (K.SEMICOLON, ";")))
    with pytest.raises(ParseError):
        p.parse_declaration()


def test_missing_semicolon_is_error():
    p = Parser(tokens((K.INT, "int"), (K.IDENTIFIERLIT, "x")))
    with pytest.raises(ParseError):
        p.parse_declaration()


def test_missing_name_is_error():
    p = Parser(tokens((K.INT, "int"), (K.ASSIGNMENT, "="), (K.INTLIT, "5"), (K.SEMICOLON, ";")))
    with pytest.raises(ParseError):
        p.parse_declaration()


def test_keyword_as_name_is_error():
    # int while;   keywords are reserved (spec 2.4)
    p = Parser(tokens((K.INT, "int"), (K.WHILE, "while"), (K.SEMICOLON, ";")))
    with pytest.raises(ParseError):
        p.parse_declaration()


def test_builtin_name_parses():
    # int rows;   parses fine; rejecting built-in names is semantic (spec 2.5, 5.1)
    d = Parser(tokens((K.INT, "int"), (K.IDENTIFIERLIT, "rows"), (K.SEMICOLON, ";"))).parse_declaration()
    assert d.declared_identifier == "rows"


def test_error_reports_line():
    toks = [Token(K.INT, "int", 7), Token(K.IDENTIFIERLIT, "x", 7), Token(K.EOF, "", 7)]
    with pytest.raises(ParseError) as err:
        Parser(toks).parse_declaration()
    assert err.value.line == 7