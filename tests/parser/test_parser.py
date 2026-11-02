"""Integration tests: print statements and whole-program parsing (spec sections 3 and 8)."""

import pytest

from src.lexer.lexer import lexer
from src.parser.parser import Parser, ParseError
from src.ast.ast_node import (
    Program, PrintStmt, DeclarationStmt, AssignmentStmt, IfStmt, WhileStmt, BlockStmt,
    LiteralExpr, VariableExpr, BinaryExpr, MatrixAccessExpr, MatrixLiteralExpr,
)
from src.semantic.type import IntType, FloatType, MatrixType


def stmt(source):
    """Lex `source` and parse it as one statement."""
    return Parser(lexer(source)).parse_statement()


def program(source):
    """Lex `source` and parse it as a whole program."""
    return Parser(lexer(source)).parse_program()


# --- print statements ------------------------------------------------------

def test_print_string():
    node = stmt('print("hello");')
    assert isinstance(node, PrintStmt)
    assert len(node.arguments) == 1
    assert isinstance(node.arguments[0], LiteralExpr)
    assert node.arguments[0].value == "hello"


def test_print_expression():
    node = stmt("print(x);")
    assert isinstance(node.arguments[0], VariableExpr)


def test_print_arithmetic_expression():
    node = stmt("print(1 + 2);")
    assert isinstance(node.arguments[0], BinaryExpr)


def test_print_string_and_expression():
    node = stmt('print("sum =", x);')
    assert len(node.arguments) == 2
    assert node.arguments[0].value == "sum ="
    assert isinstance(node.arguments[1], VariableExpr)


def test_print_many_arguments():
    node = stmt('print("a", x, "b", y);')
    assert len(node.arguments) == 4


def test_print_resolves_newline_escape():
    node = stmt('print("line\\nbreak");')
    assert node.arguments[0].value == "line\nbreak"


def test_print_resolves_quote_escape():
    node = stmt('print("say \\"hi\\"");')
    assert node.arguments[0].value == 'say "hi"'


def test_print_resolves_backslash_escape():
    node = stmt('print("a\\\\b");')
    assert node.arguments[0].value == "a\\b"


def test_print_empty_string():
    node = stmt('print("");')
    assert node.arguments[0].value == ""


def test_print_records_line_number():
    node = stmt("\nprint(x);")
    assert node.line == 2


def test_print_allowed_as_if_body():
    node = stmt('if (c) print("yes");')
    assert isinstance(node.then_branch, PrintStmt)


def test_print_allowed_in_block():
    node = stmt('{ print("a"); print("b"); }')
    assert all(isinstance(s, PrintStmt) for s in node.statements)


# --- print syntax errors ---------------------------------------------------

def test_print_no_arguments():
    with pytest.raises(ParseError):
        stmt("print();")


def test_print_missing_left_paren():
    with pytest.raises(ParseError):
        stmt('print "a";')


def test_print_missing_right_paren():
    with pytest.raises(ParseError):
        stmt('print("a";')


def test_print_missing_semicolon():
    with pytest.raises(ParseError):
        stmt('print("a")')


def test_print_missing_comma_between_arguments():
    with pytest.raises(ParseError):
        stmt('print("a" "b");')


def test_print_trailing_comma():
    with pytest.raises(ParseError):
        stmt('print("a",);')


# --- whole programs --------------------------------------------------------

def test_empty_program():
    node = program("")
    assert isinstance(node, Program)
    assert node.statements == []


def test_program_with_only_comments():
    node = program("// nothing here\n/* or here */")
    assert node.statements == []


def test_program_statement_kinds_and_order():
    node = program('int x = 5; x = x + 1; print(x);')
    assert len(node.statements) == 3
    assert isinstance(node.statements[0], DeclarationStmt)
    assert isinstance(node.statements[1], AssignmentStmt)
    assert isinstance(node.statements[2], PrintStmt)


def test_program_declaration_types():
    node = program("int a; float b; matrix<2, 3> c;")
    assert isinstance(node.statements[0].declared_type, IntType)
    assert isinstance(node.statements[1].declared_type, FloatType)
    assert isinstance(node.statements[2].declared_type, MatrixType)


def test_program_declaration_with_and_without_initializer():
    node = program("int a; int b = 2;")
    assert node.statements[0].initializer is None
    assert isinstance(node.statements[1].initializer, LiteralExpr)


def test_program_nested_control_flow():
    node = program("int n = 3; while (n) { if (n) n = n - 1; else n = 0; }")
    loop = node.statements[1]
    assert isinstance(loop, WhileStmt)
    assert isinstance(loop.loop_body, BlockStmt)
    assert isinstance(loop.loop_body.statements[0], IfStmt)


def test_program_indexed_assignment():
    node = program("matrix<2, 2> M; M[1, 2] = 5.0;")
    assert isinstance(node.statements[1].target, MatrixAccessExpr)


def test_program_statements_record_their_own_lines():
    node = program("int x;\nx = 1;\nprint(x);")
    assert [s.line for s in node.statements] == [1, 2, 3]


# --- the example programs from spec section 8 ------------------------------

SPEC_8_1 = """
// Basic matrix arithmetic
matrix<2, 2> A = [1, 2; 3, 4];
matrix<2, 2> B = [5, 6; 7, 8];
matrix<2, 2> sum = A + B;
matrix<2, 2> product = A * B;
matrix<2, 2> scaled = A * 2.0;
print("A + B =", sum);
print("A * B =", product);
print("A * 2 =", scaled);
"""

SPEC_8_2 = """
matrix<2, 2> A = [3, 2; -1, 1];
matrix<2, 1> b = [7; 1];
float det = determinant(A);
if (det) {
    matrix<2, 2> A_inv = inverse(A);
    matrix<2, 1> x = A_inv * b;
    print("Solution vector x =", x);
    matrix<2, 1> check = A * x;
    print("Verification (Ax) =", check);
} else {
    print("System has no unique solution");
}
"""

SPEC_8_3 = """
matrix<2, 2> A = [1, 1; 1, 0];
matrix<2, 2> result = [1, 0; 0, 1];
int n = 5;
while (n) {
    result = result * A;
    n = n - 1;
}
print("A^5 =", result);
"""

SPEC_8_4 = """
matrix<3, 3> M = [1, 2, 3; 4, 5, 6; 7, 8, 9];
int i = rows(M);
float trace = 0.0;
while (i) {
    trace = trace + M[i, i];
    i = i - 1;
}
print("trace = ", trace);
"""


def test_spec_example_matrix_arithmetic():
    node = program(SPEC_8_1)
    assert len(node.statements) == 8
    assert all(isinstance(s, DeclarationStmt) for s in node.statements[:5])
    assert all(isinstance(s, PrintStmt) for s in node.statements[5:])
    assert isinstance(node.statements[0].initializer, MatrixLiteralExpr)


def test_spec_example_linear_system_solver():
    node = program(SPEC_8_2)
    assert len(node.statements) == 4
    branch = node.statements[3]
    assert isinstance(branch, IfStmt)
    assert isinstance(branch.then_branch, BlockStmt)
    assert len(branch.then_branch.statements) == 5
    assert isinstance(branch.else_branch, BlockStmt)
    assert len(branch.else_branch.statements) == 1


def test_spec_example_matrix_power():
    node = program(SPEC_8_3)
    assert len(node.statements) == 5
    loop = node.statements[3]
    assert isinstance(loop, WhileStmt)
    assert len(loop.loop_body.statements) == 2
    assert isinstance(node.statements[4], PrintStmt)


def test_spec_example_indexing_and_builtins():
    node = program(SPEC_8_4)
    assert len(node.statements) == 5
    loop = node.statements[3]
    first = loop.loop_body.statements[0]
    assert isinstance(first, AssignmentStmt)
    assert isinstance(first.value, BinaryExpr)
    assert isinstance(first.value.right_operand, MatrixAccessExpr)


# --- whole-program syntax errors -------------------------------------------

def test_program_missing_semicolon():
    with pytest.raises(ParseError):
        program("int x = 5")


def test_program_stray_closing_brace():
    with pytest.raises(ParseError):
        program("x = 1; }")


def test_program_junk_after_valid_statements():
    """parse_program must consume all input, not stop after a valid prefix."""
    with pytest.raises(ParseError):
        program("x = 1; )")


def test_program_unterminated_block():
    with pytest.raises(ParseError):
        program("{ x = 1;")


def test_program_declaration_as_embedded_statement():
    """Spec 3.2: `if (c) int x = 1;` does not parse."""
    with pytest.raises(ParseError):
        program("if (c) int x = 1;")


def test_program_expression_is_not_a_statement():
    with pytest.raises(ParseError):
        program("5;")


def test_program_chained_assignment_rejected():
    with pytest.raises(ParseError):
        program("x = y = 0;")


def test_program_error_reports_correct_line():
    with pytest.raises(ParseError) as info:
        program("x = 1;\ny = ;")
    assert info.value.line == 2