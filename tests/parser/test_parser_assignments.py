"""Unit tests for parse_assignment() (spec section 3).

Covers both forms:
    IDENTIFIER '=' expression ';'
    IDENTIFIER '[' expression ',' expression ']' '=' expression ';'


Lexer is merged so no need to hand build tokens ^o^
"""

import pytest

from src.lexer.lexer import lexer
from src.parser.parser import Parser, ParseError
from src.ast.ast_node import AssignmentStmt, LiteralExpr, VariableExpr, UnaryExpr, MatrixAccessExpr


def parse(source):
    """Lex `source` and return a Parser ready to parse it."""
    return Parser(lexer(source))


# --- simple form: x = expression; ------------------------------------------

def test_assign_int_literal():
    stmt = parse("x = 5;").parse_assignment()
    assert isinstance(stmt, AssignmentStmt)
    assert stmt.target == "x"
    assert stmt.line == 1
    assert isinstance(stmt.value, LiteralExpr)
    assert stmt.value.value == 5


def test_assign_float_literal():
    stmt = parse("x = 2.5;").parse_assignment()
    assert isinstance(stmt.value, LiteralExpr)
    assert stmt.value.value == 2.5


def test_assign_variable():
    stmt = parse("x = y;").parse_assignment()
    assert stmt.target == "x"
    assert isinstance(stmt.value, VariableExpr)
    assert stmt.value.identifier == "y"


def test_assign_unary_minus():
    stmt = parse("x = -3;").parse_assignment()
    assert isinstance(stmt.value, UnaryExpr)


def test_assign_records_line_number():
    stmt = parse("\n\nx = 5;").parse_assignment()
    assert stmt.line == 3


# --- indexed form: M[i, j] = expression; -----------------------------------

def test_indexed_assignment_literal_indices():
    stmt = parse("M[1, 2] = 5.0;").parse_assignment()
    assert isinstance(stmt, AssignmentStmt)
    assert isinstance(stmt.target, MatrixAccessExpr)
    assert stmt.target.matrix_name == "M"
    assert stmt.target.row_index.value == 1
    assert stmt.target.column_index.value == 2
    assert stmt.value.value == 5.0


def test_indexed_assignment_variable_indices():
    stmt = parse("M[i, j] = x;").parse_assignment()
    assert isinstance(stmt.target.row_index, VariableExpr)
    assert isinstance(stmt.target.column_index, VariableExpr)
    assert stmt.target.row_index.identifier == "i"
    assert stmt.target.column_index.identifier == "j"


# --- syntax errors ---------------------------------------------------------

def test_missing_assignment_operator():
    with pytest.raises(ParseError):
        parse("x 5;").parse_assignment()


def test_missing_value():
    with pytest.raises(ParseError):
        parse("x = ;").parse_assignment()


def test_missing_semicolon():
    with pytest.raises(ParseError):
        parse("x = 5").parse_assignment()


def test_chained_assignment_rejected():
    """Spec 5.6: assignment is a statement, so x = y = 0; does not parse."""
    with pytest.raises(ParseError):
        parse("x = y = 0;").parse_assignment()


def test_indexed_one_index_only():
    with pytest.raises(ParseError):
        parse("M[1] = 5;").parse_assignment()


def test_indexed_missing_closing_bracket():
    with pytest.raises(ParseError):
        parse("M[1, 2 = 5;").parse_assignment()