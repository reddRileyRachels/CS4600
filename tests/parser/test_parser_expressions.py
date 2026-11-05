"""Unit tests for the expression parser (spec section 3: expression down to primary)."""

import pytest

from src.lexer.lexer import lexer
from src.parser.parser import Parser, ParseError
from src.ast.ast_node import (
    BinaryExpr, UnaryExpr, TransposeExpr, LiteralExpr, VariableExpr,
    CallExpr, MatrixAccessExpr, MatrixLiteralExpr,
)


def expr(source):
    """Lex `source` and parse it as a single expression."""
    return Parser(lexer(source)).parse_expression()


# --- primaries -------------------------------------------------------------

def test_int_literal():
    node = expr("42")
    assert isinstance(node, LiteralExpr)
    assert node.value == 42 and isinstance(node.value, int)


def test_float_literal():
    node = expr("2.5")
    assert isinstance(node, LiteralExpr)
    assert node.value == 2.5 and isinstance(node.value, float)


def test_variable():
    node = expr("x")
    assert isinstance(node, VariableExpr)
    assert node.identifier == "x"


def test_parenthesized_leaves_no_node():
    node = expr("(7)")
    assert isinstance(node, LiteralExpr)
    assert node.value == 7


def test_nested_parentheses():
    node = expr("((x))")
    assert isinstance(node, VariableExpr)

def test_nested_parentheses_with_expression():
    node = expr("(6) + ((x * 3) - 2)")
    assert isinstance(node, BinaryExpr)
    assert node.operator == "+"
    assert isinstance(node.left_operand, LiteralExpr)
    assert node.left_operand.value == 6
    assert isinstance(node.right_operand, BinaryExpr)
    assert node.right_operand.operator == "-"
    assert isinstance(node.right_operand.left_operand, BinaryExpr)
    assert node.right_operand.left_operand.operator == "*"
    assert node.right_operand.right_operand.value == 2
    assert isinstance(node.right_operand.left_operand.left_operand, VariableExpr)

# --- precedence ------------------------------------------------------------

def test_multiplication_binds_tighter_than_addition():
    node = expr("1 + 2 * 3")                       # 1 + (2 * 3)
    assert isinstance(node, BinaryExpr)
    assert node.operator == "+"
    assert node.left_operand.value == 1
    assert isinstance(node.right_operand, BinaryExpr)
    assert node.right_operand.operator == "*"


def test_parentheses_override_precedence():
    node = expr("(1 + 2) * 3")                     # (1 + 2) * 3
    assert node.operator == "*"
    assert isinstance(node.left_operand, BinaryExpr)
    assert node.left_operand.operator == "+"
    assert node.right_operand.value == 3


def test_unary_binds_tighter_than_multiplication():
    node = expr("2 * -3")                          # 2 * (-3)
    assert node.operator == "*"
    assert isinstance(node.right_operand, UnaryExpr)


# --- associativity (spec 3.1: binary operators are left-associative) --------

def test_subtraction_is_left_associative():
    node = expr("8 - 3 - 2")                       # (8 - 3) - 2
    assert node.operator == "-"
    assert node.right_operand.value == 2
    assert isinstance(node.left_operand, BinaryExpr)
    assert node.left_operand.left_operand.value == 8
    assert node.left_operand.right_operand.value == 3


def test_division_is_left_associative():
    node = expr("16 / 4 / 2")                      # (16 / 4) / 2
    assert node.operator == "/"
    assert node.right_operand.value == 2
    assert isinstance(node.left_operand, BinaryExpr)
    assert node.left_operand.left_operand.value == 16


def test_addition_chain_is_left_associative():
    node = expr("a + b + c")
    assert isinstance(node.left_operand, BinaryExpr)
    assert node.right_operand.identifier == "c"


# --- unary minus and transpose ---------------------------------------------

def test_unary_minus():
    node = expr("-x")
    assert isinstance(node, UnaryExpr)
    assert node.operator == "-"
    assert node.operand.identifier == "x"


def test_double_unary_minus():
    node = expr("--x")                             # -(-x)
    assert isinstance(node, UnaryExpr)
    assert isinstance(node.operand, UnaryExpr)

def test_unary_minus_literal():
    node = expr("-6")
    assert isinstance(node, UnaryExpr)
    assert node.operator == "-"
    assert node.operand.value == 6


def test_transpose():
    node = expr("A'")
    assert isinstance(node, TransposeExpr)
    assert node.operand.identifier == "A"


def test_double_transpose():
    node = expr("A''")
    assert isinstance(node, TransposeExpr)
    assert isinstance(node.operand, TransposeExpr)


def test_unary_minus_applies_after_transpose():
    node = expr("-A'")                             # -(A')  (spec 3.1)
    assert isinstance(node, UnaryExpr)
    assert isinstance(node.operand, TransposeExpr)


def test_transpose_binds_tighter_than_multiplication():
    node = expr("a - b * c'")                      # a - (b * (c'))
    assert node.operator == "-"
    product = node.right_operand
    assert product.operator == "*"
    assert isinstance(product.right_operand, TransposeExpr)


# --- calls and indexing ----------------------------------------------------

def test_call_one_argument():
    node = expr("determinant(A)")
    assert isinstance(node, CallExpr)
    assert node.function_name == "determinant"
    assert len(node.arguments) == 1
    assert node.arguments[0].identifier == "A"


def test_call_with_expression_argument():
    node = expr("toFloat(n + 1)")
    assert isinstance(node.arguments[0], BinaryExpr)


def test_index_access():
    node = expr("M[1, 2]")
    assert isinstance(node, MatrixAccessExpr)
    assert node.matrix_name == "M"
    assert node.row_index.value == 1
    assert node.column_index.value == 2


def test_index_with_variable_indices():
    node = expr("M[i, j]")
    assert node.row_index.identifier == "i"
    assert node.column_index.identifier == "j"


def test_index_inside_arithmetic():
    node = expr("trace + M[i, i]")
    assert isinstance(node, BinaryExpr)
    assert isinstance(node.right_operand, MatrixAccessExpr)


# --- matrix literals -------------------------------------------------------

def test_matrix_literal_2x2():
    node = expr("[1, 2; 3, 4]")
    assert isinstance(node, MatrixLiteralExpr)
    assert len(node.rows) == 2
    assert [e.value for e in node.rows[0]] == [1, 2]
    assert [e.value for e in node.rows[1]] == [3, 4]


def test_matrix_literal_column_vector():
    node = expr("[7; 1]")
    assert len(node.rows) == 2
    assert len(node.rows[0]) == 1


def test_matrix_literal_row_vector():
    node = expr("[1, 2, 3]")
    assert len(node.rows) == 1
    assert len(node.rows[0]) == 3


def test_matrix_literal_with_negative_and_float():
    node = expr("[3, 2; -1, 1.5]")
    assert isinstance(node.rows[1][0], UnaryExpr)
    assert node.rows[1][1].value == 1.5


def test_matrix_literal_ragged_rows_still_parse():
    """Ragged rows are a semantic error (spec 7.1), not a syntax error."""
    node = expr("[1, 2; 3]")
    assert len(node.rows[0]) == 2
    assert len(node.rows[1]) == 1




# --- syntax errors ---------------------------------------------------------

def test_missing_closing_paren():
    with pytest.raises(ParseError):
        expr("(3 + 4")


def test_missing_operand_after_operator():
    with pytest.raises(ParseError):
        expr("1 +")


def test_missing_expression():
    with pytest.raises(ParseError):
        expr(")")


def test_empty_expression():
    with pytest.raises(ParseError):
        expr("")


def test_call_missing_closing_paren():
    with pytest.raises(ParseError):
        expr("determinant(A")


def test_call_with_no_arguments():
    """arg_list needs at least one expression (spec 3)."""
    with pytest.raises(ParseError):
        expr("f()")


def test_index_one_index_only():
    with pytest.raises(ParseError):
        expr("M[1]")


def test_index_missing_closing_bracket():
    with pytest.raises(ParseError):
        expr("M[1, 2")


def test_matrix_literal_missing_closing_bracket():
    with pytest.raises(ParseError):
        expr("[1, 2; 3, 4")


def test_empty_matrix_literal():
    with pytest.raises(ParseError):
        expr("[]")


''' COMPLEX EXPRESSION PARSING TESTS '''


def test_complex_expression_many_binary():
    node = expr("1 + 2 * 3 - 4 / 2")     # (1 + (2 * 3)) - (4 / 2)
    assert isinstance(node, BinaryExpr)
    assert node.operator == "-"
    assert isinstance(node.right_operand, BinaryExpr)
    assert node.right_operand.operator == "/"
    assert node.right_operand.left_operand.value == 4
    assert node.right_operand.right_operand.value == 2
    assert isinstance(node.left_operand, BinaryExpr)
    assert node.left_operand.left_operand.value == 1
    assert isinstance(node.left_operand.right_operand, BinaryExpr)
    assert node.left_operand.right_operand.left_operand.value == 2
    assert node.left_operand.right_operand.right_operand.value == 3