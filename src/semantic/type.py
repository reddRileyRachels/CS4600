class Type:
    def __init__(self):
        pass


class IntType(Type):
    def __init__(self):
        super().__init__()


class FloatType(Type):
    def __init__(self):
        super().__init__()


class MatrixType(Type):

    def __init__(self, rows: int, cols: int):
        super().__init__()
        self.rows = rows
        self.cols = cols