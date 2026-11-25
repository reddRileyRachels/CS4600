import pytest

from src.lexer.lexer import lexer
from src.parser.parser import Parser
from src.semantic.symbol_table import SemanticError
from src.semantic.type_checker import TypeChecker


def analyze(source):
    program = Parser(lexer(source)).parse_program()
    return TypeChecker().check_program(program)


def assert_error(source, line=None, match=None):
    with pytest.raises(SemanticError, match=match) as err:
        analyze(source)
    if line is not None:
        assert err.value.line == line
    return err.value


M22 = "matrix<2,2> A = [1,2;3,4]; "
M23 = "matrix<2,3> A = [1,2,3;4,5,6]; "


# --- spec 8: example programs through the real TypeChecker -------------------
# paste SPEC_8_1 .. SPEC_8_4 here (copy from test_scope_validation.py)
SPEC_8_1 = """
matrix<2, 2> A = [1, 2; 3, 4];
matrix<2, 2> B = [5, 6; 7, 8];
matrix<2, 2> sum     = A + B;
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
matrix<2, 2> A      = [1, 1; 1, 0];
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

@pytest.mark.parametrize("source", [SPEC_8_1, SPEC_8_2, SPEC_8_3, SPEC_8_4],
                         ids=["8.1", "8.2", "8.3", "8.4"])
def test_spec_examples_pass_type_checker(source):
    analyze(source)


# --- spec 5.9: conditions -----------------------------------------------------

@pytest.mark.parametrize("keyword", ["if", "while"])
def test_matrix_condition_is_rejected(keyword):          # fails until fix
    assert_error(f"{M22}\n{keyword} (A) {{ print(1); }}",
                 line=2, match="condition must be int or float")


@pytest.mark.parametrize("cond", ["n", "f", "n - 1", "f * 2.0"])
def test_scalar_conditions_are_accepted(cond):
    analyze(f"int n = 1; float f = 1.0; if ({cond}) {{ print(1); }}")


# --- spec 5.5: indexing (1-based) ----------------------------------------------

def test_valid_one_based_indices_are_accepted():          # fails until fix
    analyze(M22 + "float x = A[1,1]; float y = A[2,2];")


@pytest.mark.parametrize("idx", ["0,1", "1,0", "3,1", "1,3", "-1,1"])
def test_constant_index_out_of_range_is_rejected(idx):    # some fail until fix
    assert_error(M22 + f"float x = A[{idx}];", match="out of bounds")


def test_non_constant_index_is_accepted_statically():
    analyze(M22 + "int i = 1; float x = A[i, i];")


def test_float_index_is_rejected():
    assert_error(M22 + "float x = A[1.0, 1];")


def test_indexing_a_scalar_is_rejected():
    assert_error("int n = 1; float x = n[1, 1];", match="requires a matrix")


def test_indexed_assignment_accepts_literal_and_float():
    analyze(M22 + "float f = 2.0; A[1,1] = f; A[2,2] = 3;")


def test_indexed_assignment_rejects_int_variable():
    assert_error(M22 + "int n = 1; A[1,1] = n;")


def test_indexed_assignment_rejects_out_of_range_constant():   # fails until fix
    assert_error(M22 + "A[0,1] = 1.0;", match="out of bounds")


# --- spec 5.2: binary operators -----------------------------------------------

def test_float_divided_by_matrix_is_rejected():
    assert_error(M22 + "matrix<2,2> B = 2.0 / A;")


def test_matrix_divided_by_matrix_is_rejected():
    assert_error(M22 + "matrix<2,2> B = A / A;")


def test_matrix_divided_by_int_variable_is_rejected():
    assert_error(M22 + "int n = 2; matrix<2,2> B = A / n;")


def test_int_times_float_is_rejected():
    assert_error("int a = 1; float b = 2.0; float c = a * b;")


def test_matrix_1x1_cannot_initialize_float():
    assert_error("matrix<1,1> A = [1]; float x = A;")


# --- spec 5.3 / 5.4: unary minus and transpose -------------------------------

def test_unary_minus_on_all_types():
    analyze(M22 + "int a = 1; float f = 1.0; "
                  "int b = -a; float g = -f; matrix<2,2> B = -A;")


def test_transpose_of_scalar_is_rejected():
    assert_error("int n = 1; int m = n';", match="requires a matrix")


def test_transpose_swaps_dimensions():
    analyze(M23 + "matrix<3,2> B = A';")


def test_transpose_wrong_declared_shape_is_rejected():
    assert_error(M23 + "matrix<2,3> B = A';")


def test_double_transpose_has_original_type():
    analyze(M23 + "matrix<2,3> B = A'';")


def test_negated_transpose():
    analyze(M23 + "matrix<3,2> B = -A';")


# --- spec 5.7: conversion built-ins -------------------------------------------

def test_tofloat_rejects_float_argument():                # fails until fix
    assert_error("float x = toFloat(1.5);")


def test_toint_rejects_int_argument():                    # fails until fix
    assert_error("int x = toInt(2);")


def test_conversions_accept_correct_argument_types():
    analyze("float f = toFloat(4); int i = toInt(4.5);")


# --- spec 5.1: scope rules through the TypeChecker ---------------------------

def test_undeclared_variable_has_line_number():
    assert_error("z = 1;", line=1, match="not declared")


def test_use_before_declaration():
    assert_error("print(x);\nint x = 1;", line=1)


def test_redeclaration_same_scope():
    assert_error("int x = 1;\nfloat x = 2.0;", line=2)


@pytest.mark.parametrize("name", ["rows", "cols", "determinant", "inverse", "toFloat", "toInt"])
def test_declaring_builtin_name_is_rejected(name):
    assert_error(f"int {name} = 1;")


def test_shadowing_is_legal():
    analyze("int x = 1; { float x = 2.0; print(x); }")


def test_shadow_uses_inner_type():
    assert_error("int x = 1; { float x = 2.0; int y = x; }")


def test_block_variable_not_visible_after_block():
    assert_error("{ int y = 1; }\nprint(y);", line=2)


def test_initializer_cannot_use_its_own_name():
    assert_error("int x = x;")


def test_shadow_initializer_uses_outer_variable():
    analyze("int x = 1; { int x = x + 1; }")


def test_undeclared_matrix_in_indexed_assignment():
    assert_error("B[1,1] = 2.0;")


def test_type_error_reports_line_number():
    assert_error("int x = 1;\nint y = 2.5;", line=2)