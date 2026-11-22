"""Unit tests for if/while/block parsing and statement dispatch (spec section 3)."""

import pytest

from src.lexer.lexer import lexer
from src.parser.parser import Parser, ParseError
from src.ast.ast_node import (
    IfStmt, WhileStmt, BlockStmt, AssignmentStmt, DeclarationStmt,
    VariableExpr, LiteralExpr, BinaryExpr,
)


def stmt(source):
    """Lex `source` and parse it as one statement."""
    return Parser(lexer(source)).parse_statement()


# --- while -----------------------------------------------------------------

def test_while_with_single_statement_body():
    node = stmt("while (n) n = n - 1;")
    assert isinstance(node, WhileStmt)
    assert isinstance(node.condition, VariableExpr)
    assert isinstance(node.loop_body, AssignmentStmt)


def test_while_with_block_body():
    node = stmt("while (n) { result = result * A; n = n - 1; }")   # spec 8.3
    assert isinstance(node.loop_body, BlockStmt)
    assert len(node.loop_body.statements) == 2


def test_while_condition_is_expression():
    node = stmt("while (n - 1) x = 0;")
    assert isinstance(node.condition, BinaryExpr)


def test_while_records_line_number():
    node = stmt("\nwhile (n) n = 0;")
    assert node.line == 2


# --- if / else -------------------------------------------------------------

def test_if_without_else():
    node = stmt("if (c) x = 1;")
    assert isinstance(node, IfStmt)
    assert isinstance(node.condition, VariableExpr)
    assert isinstance(node.then_branch, AssignmentStmt)
    assert node.else_branch is None


def test_if_with_else():
    node = stmt("if (c) x = 1; else x = 2;")
    assert isinstance(node.then_branch, AssignmentStmt)
    assert isinstance(node.else_branch, AssignmentStmt)


def test_if_else_with_blocks():
    node = stmt("if (det) { x = 1; } else { x = 2; }")
    assert isinstance(node.then_branch, BlockStmt)
    assert isinstance(node.else_branch, BlockStmt)


def test_else_if_chain():
    node = stmt("if (a) x = 1; else if (b) x = 2; else x = 3;")
    assert isinstance(node.else_branch, IfStmt)
    assert isinstance(node.else_branch.else_branch, AssignmentStmt)


def test_dangling_else_binds_to_nearest_if():
    node = stmt("if (a) if (b) x = 1; else x = 2;")
    assert node.else_branch is None                       # outer if has no else
    inner = node.then_branch
    assert isinstance(inner, IfStmt)
    assert isinstance(inner.else_branch, AssignmentStmt)  # else went to the inner if


def test_if_records_line_number():
    node = stmt("\n\nif (c) x = 1;")
    assert node.line == 3


# --- blocks ----------------------------------------------------------------

def test_empty_block():
    node = stmt("{ }")
    assert isinstance(node, BlockStmt)
    assert node.statements == []


def test_block_with_statements():
    node = stmt("{ x = 1; y = 2; }")
    assert len(node.statements) == 2
    assert all(isinstance(s, AssignmentStmt) for s in node.statements)


def test_nested_blocks():
    node = stmt("{ { x = 1; } }")
    assert isinstance(node.statements[0], BlockStmt)
    assert isinstance(node.statements[0].statements[0], AssignmentStmt)


def test_declaration_allowed_inside_block():
    node = stmt("{ int x = 1; x = 2; }")
    assert isinstance(node.statements[0], DeclarationStmt)
    assert isinstance(node.statements[1], AssignmentStmt)


def test_declaration_allowed_inside_if_block():
    node = stmt("if (c) { int x = 1; }")                  # spec 3.2 workaround
    assert isinstance(node.then_branch.statements[0], DeclarationStmt)


def test_block_records_line_number():
    node = stmt("\n{ x = 1; }")
    assert node.line == 2


# --- statement dispatch ----------------------------------------------------

def test_statement_dispatches_to_declaration():
    assert isinstance(stmt("int x = 5;"), DeclarationStmt)


def test_statement_dispatches_to_assignment():
    assert isinstance(stmt("x = 5;"), AssignmentStmt)


def test_statement_dispatches_to_if():
    assert isinstance(stmt("if (c) x = 1;"), IfStmt)


def test_statement_dispatches_to_while():
    assert isinstance(stmt("while (c) x = 1;"), WhileStmt)


def test_statement_dispatches_to_block():
    assert isinstance(stmt("{ }"), BlockStmt)


# --- syntax errors ---------------------------------------------------------

def test_declaration_not_allowed_as_if_body():
    """Spec 3.2: `if (c) int x = 1;` does not parse."""
    with pytest.raises(ParseError):
        stmt("if (c) int x = 1;")


def test_declaration_not_allowed_as_while_body():
    with pytest.raises(ParseError):
        stmt("while (c) float y;")


def test_declaration_not_allowed_as_else_body():
    with pytest.raises(ParseError):
        stmt("if (c) x = 1; else int y = 2;")


def test_if_missing_left_paren():
    with pytest.raises(ParseError):
        stmt("if c) x = 1;")


def test_if_missing_right_paren():
    with pytest.raises(ParseError):
        stmt("if (c x = 1;")


def test_if_empty_condition():
    with pytest.raises(ParseError):
        stmt("if () x = 1;")


def test_if_missing_body():
    with pytest.raises(ParseError):
        stmt("if (c)")


def test_else_missing_body():
    with pytest.raises(ParseError):
        stmt("if (c) x = 1; else")


def test_while_missing_condition_parens():
    with pytest.raises(ParseError):
        stmt("while n x = 1;")


def test_while_missing_body():
    with pytest.raises(ParseError):
        stmt("while (n)")


def test_unterminated_block():
    with pytest.raises(ParseError):
        stmt("{ x = 1;")


def test_unterminated_nested_block():
    with pytest.raises(ParseError):
        stmt("{ { x = 1; }")


def test_stray_closing_brace_is_not_a_statement():
    with pytest.raises(ParseError):
        stmt("}")


def test_stray_else_is_not_a_statement():
    with pytest.raises(ParseError):
        stmt("else x = 1;")