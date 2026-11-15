class Type:

    def __init__(self):
        pass

    def is_scalar(self):
        return False

    def is_matrix(self):
        """True for matrix<r, c>. A matrix<1,1> is still a matrix, not a scalar."""
        return False

    def __eq__(self, other):
        return type(self) is type(other)

    def __hash__(self):
        return hash(type(self).__name__)

    def __repr__(self):
        return str(self)


class IntType(Type):
    def __init__(self):
        super().__init__()

    def is_scalar(self):
        return True

    def __str__(self):
        return "int"


class FloatType(Type):

    def __init__(self):
        super().__init__()

    def is_scalar(self):
        return True

    def __str__(self):
        return "float"


class MatrixType(Type):

    def __init__(self, rows: int, cols: int):
        super().__init__()
        self.rows = rows
        self.cols = cols

    def is_matrix(self):
        return True

    def is_square(self):
        return self.rows == self.cols

    def has_valid_dimensions(self):
        return self.rows >= 1 and self.cols >= 1

    def __eq__(self, other):
        return (
            isinstance(other, MatrixType)
            and self.rows == other.rows
            and self.cols == other.cols
        )

    def __hash__(self):
        return hash(("matrix", self.rows, self.cols))

    def __str__(self):
        return f"matrix<{self.rows},{self.cols}>"
