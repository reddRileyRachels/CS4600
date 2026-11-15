import pytest

from src.semantic.type import Type, IntType, FloatType, MatrixType


# --- construction -----------------------------------------------------------

def test_all_types_are_types():
    assert isinstance(IntType(), Type)
    assert isinstance(FloatType(), Type)
    assert isinstance(MatrixType(2, 3), Type)


def test_matrix_keeps_dimensions():
    m = MatrixType(2, 3)
    assert (m.rows, m.cols) == (2, 3)


def test_matrix_constructor_accepts_zero_dimension():
    # The parser must be able to build matrix<0,1>; rejecting it is semantic.
    m = MatrixType(0, 1)
    assert (m.rows, m.cols) == (0, 1)


# --- equality (spec 4.2) ----------------------------------------------------

def test_int_equals_int():
    assert IntType() == IntType()


def test_float_equals_float():
    assert FloatType() == FloatType()


def test_int_not_equal_float():
    # no coercion between scalars
    assert IntType() != FloatType()
    assert FloatType() != IntType()


def test_matrix_same_dimensions_equal():
    assert MatrixType(2, 3) == MatrixType(2, 3)


def test_matrix_swapped_dimensions_not_equal():
    # spec 4.1: matrix<2,3> and matrix<3,2> are different types
    assert MatrixType(2, 3) != MatrixType(3, 2)


def test_matrix_different_rows_not_equal():
    assert MatrixType(2, 3) != MatrixType(4, 3)


def test_matrix_1x1_is_not_float():
    # spec 4.1: matrix<1,1> is a matrix, not a scalar; it does not convert to float
    assert MatrixType(1, 1) != FloatType()
    assert FloatType() != MatrixType(1, 1)


def test_type_not_equal_to_other_objects():
    assert IntType() != "int"
    assert MatrixType(2, 2) != (2, 2)


def test_equal_types_have_equal_hashes():
    # lets types be used in sets / as dict keys (e.g. operator tables)
    assert hash(IntType()) == hash(IntType())
    assert hash(MatrixType(2, 3)) == hash(MatrixType(2, 3))
    assert len({IntType(), IntType(), FloatType(), MatrixType(2, 3), MatrixType(2, 3)}) == 3


# --- classification ---------------------------------------------------------

@pytest.mark.parametrize("t", [IntType(), FloatType()])
def test_int_and_float_are_scalars(t):
    assert t.is_scalar()
    assert not t.is_matrix()


def test_matrix_is_matrix_not_scalar():
    m = MatrixType(1, 1)
    assert m.is_matrix()
    assert not m.is_scalar()


def test_is_square():
    assert MatrixType(3, 3).is_square()
    assert not MatrixType(2, 3).is_square()


@pytest.mark.parametrize("rows, cols, valid", [
    (1, 1, True),
    (2, 3, True),
    (0, 1, False),
    (1, 0, False),
    (0, 0, False),
])
def test_has_valid_dimensions(rows, cols, valid):
    assert MatrixType(rows, cols).has_valid_dimensions() is valid


# --- printing (used in error messages) --------------------------------------

def test_str_int():
    assert str(IntType()) == "int"


def test_str_float():
    assert str(FloatType()) == "float"


def test_str_matrix():
    assert str(MatrixType(2, 3)) == "matrix<2,3>"


def test_repr_matches_str():
    assert repr(MatrixType(2, 3)) == "matrix<2,3>"
