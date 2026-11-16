import pytest

from src.lexer.lexer import lexer
from src.parser.parser import Parser
from src.semantic.symbol_table import SemanticError
from src.semantic.type_checker import TypeChecker


def check(source):
    program = Parser(lexer(source)).parse_program()
    return TypeChecker().check_program(program)


def assert_valid(source):
    check(source)


def assert_error(source):
    with pytest.raises(SemanticError):
        check(source)

def test_int_plus_int_is_valid():
    assert_valid("int x = 1 + 2;")


def test_float_plus_float_is_valid():
    assert_valid("float x = 1.0 + 2.0;")


def test_int_plus_float_is_rejected():
    assert_error("int x = 1; float y = 2.0; int z = x + y;")


def test_float_plus_int_is_rejected():
    assert_error("float x = 1.0; int y = 2; float z = x + y;")


def test_int_variable_cannot_initialize_float():
    assert_error("int x = 3; float y = x;")


def test_float_variable_cannot_initialize_int():
    assert_error("float x = 3.0; int y = x;")


def test_float_literal_cannot_initialize_int():
    assert_error("int x = 3.5;")


def test_int_division_expression_cannot_initialize_float():
    assert_error("float x = 3 / 2;")


def test_int_assignment_to_float_variable_is_rejected_for_variable_rhs():
    assert_error("int n = 3; float x; x = n;")


def test_float_assignment_to_int_variable_is_rejected():
    assert_error("int x; x = 3.0;")


def test_integer_literal_can_initialize_float():
    assert_valid("float x = 3;")


def test_negative_integer_literal_can_initialize_float():
    assert_valid("float x = -3;")


def test_integer_literal_can_be_assigned_to_float():
    assert_valid("float x; x = 3;")


def test_negative_integer_literal_can_be_assigned_to_float():
    assert_valid("float x; x = -3;")


def test_context_typing_does_not_propagate_into_arithmetic():
    assert_error("float x; x = 3 + 0;")


def test_integer_literals_are_allowed_in_matrix_literal():
    assert_valid("matrix<2,2> A = [1,2;3,4];")


def test_negative_integer_literals_are_allowed_in_matrix_literal():
    assert_valid("matrix<2,2> A = [-1,2;-3,4];")


def test_float_literals_are_allowed_in_matrix_literal():
    assert_valid("matrix<2,2> A = [1.0,2.0;3.0,4.0];")


def test_integer_variable_is_not_context_typed_in_matrix_literal():
    assert_error("int n = 2; matrix<1,1> A = [n];")


def test_arithmetic_expression_is_not_context_typed_in_matrix_literal():
    assert_error("matrix<1,1> A = [1 + 2];")


# §4.3 rule 2: only direct integer literals may act as matrix scalar operands.
def test_matrix_times_integer_literal_is_valid():
    assert_valid("matrix<2,2> A = [1,2;3,4]; matrix<2,2> B = A * 2;")


def test_integer_literal_times_matrix_is_valid():
    assert_valid("matrix<2,2> A = [1,2;3,4]; matrix<2,2> B = 2 * A;")


def test_matrix_divided_by_integer_literal_is_valid():
    assert_valid("matrix<2,2> A = [1,2;3,4]; matrix<2,2> B = A / 2;")


def test_matrix_times_float_literal_is_valid():
    assert_valid("matrix<2,2> A = [1,2;3,4]; matrix<2,2> B = A * 2.0;")


def test_matrix_times_integer_variable_is_rejected():
    assert_error(
        "matrix<2,2> A = [1,2;3,4]; "
        "int n = 2; matrix<2,2> B = A * n;"
    )


def test_matrix_times_integer_expression_is_rejected():
    assert_error(
        "matrix<2,2> A = [1,2;3,4]; "
        "matrix<2,2> B = A * (1 + 1);"
    )


def test_matrix_plus_scalar_is_rejected():
    assert_error(
        "matrix<2,2> A = [1,2;3,4]; "
        "matrix<2,2> B = A + 2.0;"
    )


def test_float_times_matrix_is_valid():
    assert_valid(
        "matrix<2,2> A = [1,2;3,4]; "
        "matrix<2,2> B = 2.0 * A;"
    )


def test_scope_keeps_variable_types_available():
    assert_valid("int x = 1; { float x = 2; float y = x; } float z = 3;")
