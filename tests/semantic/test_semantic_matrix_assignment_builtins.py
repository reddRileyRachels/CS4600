import pytest

from src.lexer.lexer import lexer
from src.parser.parser import Parser
from src.semantic.symbol_table import SemanticError
from src.semantic.type_checker import TypeChecker


def analyze(source):
    program = Parser(lexer(source)).parse_program()
    return TypeChecker().check_program(program)


def test_matrix_addition_requires_equal_dimensions():
    analyze(
        "matrix<2,2> A = [1,2;3,4]; "
        "matrix<2,2> B = [1,2;3,4]; "
        "matrix<2,2> C = A + B;"
    )


def test_matrix_addition_rejects_different_dimensions():
    with pytest.raises(SemanticError, match="requires equal dimensions"):
        analyze(
            "matrix<2,2> A = [1,2;3,4]; "
            "matrix<2,3> B = [1,2,3;4,5,6]; "
            "matrix<2,2> C = A + B;"
        )


def test_matrix_subtraction_rejects_different_dimensions():
    with pytest.raises(SemanticError, match="requires equal dimensions"):
        analyze(
            "matrix<1,2> A = [1,2]; matrix<2,1> B = [1;2]; "
            "matrix<1,2> C = A - B;"
        )


def test_matrix_multiplication_checks_inner_dimensions_and_result_shape():
    analyze(
        "matrix<2,3> A = [1,2,3;4,5,6]; "
        "matrix<3,4> B = [1,2,3,4;5,6,7,8;9,10,11,12]; "
        "matrix<2,4> C = A * B;"
    )


def test_matrix_multiplication_rejects_incompatible_inner_dimensions():
    with pytest.raises(SemanticError, match="left columns to equal right rows"):
        analyze(
            "matrix<2,3> A = [1,2,3;4,5,6]; "
            "matrix<2,4> B = [1,2,3,4;5,6,7,8]; "
            "matrix<2,4> C = A * B;"
        )


def test_matrix_assignment_requires_exact_shape():
    with pytest.raises(SemanticError, match="assignment requires matrix<2,2>"):
        analyze(
            "matrix<2,2> A = [1,2;3,4]; "
            "matrix<2,3> B = [1,2,3;4,5,6]; A = B;"
        )


def test_matrix_initializer_requires_exact_shape():
    with pytest.raises(SemanticError, match="initializer requires matrix<2,2>"):
        analyze("matrix<2,2> A = [1,2,3;4,5,6];")


def test_matrix_literal_rejects_ragged_rows():
    with pytest.raises(SemanticError, match="matrix literal row 2"):
        analyze("matrix<2,2> A = [1,2;3];")


def test_matrix_dimensions_must_be_positive():
    with pytest.raises(SemanticError, match="positive dimensions"):
        analyze("matrix<0,2> A;")


def test_matrix_index_checks_integer_type_and_static_bounds():
    with pytest.raises(SemanticError, match="out of bounds"):
        analyze("matrix<2,2> A = [1,2;3,4]; float x = A[2,0];")


def test_indexed_assignment_requires_matrix_target_and_float_value():
    with pytest.raises(SemanticError, match="indexed assignment requires float"):
        analyze("matrix<2,2> A = [1,2;3,4]; A[0,0] = A;")


def test_rows_cols_and_numeric_conversions_accept_valid_arguments():
    analyze(
        "matrix<2,2> A = [1,2;3,4]; "
        "int r = rows(A); int c = cols(A); "
        "float f = toFloat(4); int i = toInt(4.5);"
    )


@pytest.mark.parametrize("call", ["rows(1)", "cols(1)", "determinant(1)", "inverse(1)"])
def test_matrix_builtins_reject_non_matrix_arguments(call):
    with pytest.raises(SemanticError, match="requires a matrix"):
        analyze(f"int x = {call};")


@pytest.mark.parametrize("call", ["cols(1,2)", "determinant(1,2)"])
def test_builtins_validate_argument_count(call):
    with pytest.raises(SemanticError, match="expects 1 argument"):
        analyze(f"int x = {call};")


@pytest.mark.parametrize("call", ["determinant(A)", "inverse(A)"])
def test_square_matrix_builtins_reject_rectangular_matrices(call):
    with pytest.raises(SemanticError, match="requires a square matrix"):
        analyze(f"matrix<2,3> A = [1,2,3;4,5,6]; float x = {call};")


def test_inverse_preserves_matrix_dimensions():
    analyze(
        "matrix<3,3> A = [1,2,3;4,5,6;7,8,9]; "
        "matrix<3,3> B = inverse(A);"
    )


def test_conversion_builtins_reject_matrix_arguments():
    with pytest.raises(SemanticError, match="requires a scalar numeric argument"):
        analyze("matrix<1,1> A = [1]; float x = toFloat(A);")


def test_unknown_function_is_rejected():
    with pytest.raises(SemanticError, match="unknown built-in function"):
        analyze("int x = mystery(1);")