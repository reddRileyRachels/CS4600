from src.ast.ast_node import (
    AssignmentStmt,
    BinaryExpr,
    BlockStmt,
    CallExpr,
    DeclarationStmt,
    LiteralExpr,
    MatrixAccessExpr,
    MatrixLiteralExpr,
    PrintStmt,
    Program,
    TransposeExpr,
    UnaryExpr,
    VariableExpr,
    IfStmt,
    WhileStmt,
)
from src.semantic.symbol import Symbol
from src.semantic.symbol_table import SemanticError, SymbolTable
from src.semantic.type import FloatType, IntType, MatrixType


class TypeChecker:
    """Performs name resolution and static type/shape checks for MatLang."""

    def __init__(self, symbol_table=None):
        self.symbol_table = symbol_table if symbol_table is not None else SymbolTable()

    def _error(self, message, line):
        raise SemanticError(message, line if line is not None else 1)

    @staticmethod
    def _is_int_literal(expr):
        return TypeChecker._static_int_value(expr) is not None

    @staticmethod
    def _static_int_value(expr):
        """Return an integer value for an integer literal (including -N)."""
        if isinstance(expr, LiteralExpr) and type(expr.value) is int:
            return expr.value
        if (
            isinstance(expr, UnaryExpr)
            and expr.operator == "-"
            and isinstance(expr.operand, LiteralExpr)
            and type(expr.operand.value) is int
        ):
            return -expr.operand.value
        return None

    def _expect_same(self, actual, expected, line, context):
        if actual != expected:
            self._error(f"{context} requires {expected}, got {actual}", line)

    def _expect_matrix(self, actual, line, context):
        if not isinstance(actual, MatrixType):
            self._error(f"{context} requires a matrix, got {actual}", line)

    def _check_condition(self, expr, context):
        t = self.check_expression(expr)
        """Spec 5.9: if/while conditions must be a scalar (int or float)."""
        if not isinstance(t, (IntType, FloatType)):
            self._error(f"{context} condition must be int or float, got {t}",
                        getattr(expr, "line", None))

    def _check_matrix_indices(self, matrix_type, row_expr, col_expr, line):
        row_type = self.check_expression(row_expr)
        col_type = self.check_expression(col_expr)
        self._expect_same(row_type, IntType(), getattr(row_expr, "line", line), "matrix row index")
        self._expect_same(col_type, IntType(), getattr(col_expr, "line", line), "matrix column index")

        row = self._static_int_value(row_expr)
        col = self._static_int_value(col_expr)
        # MatLang spec says indices are 1 through r. Dynamic indices are type-checked here;
        # their run-time values cannot be bounded by this static checker.
        if row is not None and not 1 <= row < matrix_type.rows:
            self._error(
                f"matrix row index {row} is out of bounds for {matrix_type.rows} rows",
                line,
            )
        if col is not None and not 1 <= col < matrix_type.cols:
            self._error(
                f"matrix column index {col} is out of bounds for {matrix_type.cols} columns",
                line,
            )

    def check_program(self, program):
        if not isinstance(program, Program):
            self._error("expected a Program AST", getattr(program, "line", 1))
        for statement in program.statements:
            self.check_statement(statement)
        return program

    def check_expression(self, expr, expected_type=None):
        if isinstance(expr, LiteralExpr):
            if isinstance(expr.value, str):
                self._error("string literals are only valid as print arguments", expr.line)
            if type(expr.value) is int:
                return FloatType() if isinstance(expected_type, FloatType) else IntType()
            if type(expr.value) is float:
                return FloatType()
            self._error("unsupported literal", expr.line)

        if isinstance(expr, VariableExpr):
            symbol = self.symbol_table.lookup(expr.identifier)
            if symbol is None:
                self._error(f"'{expr.identifier}' is not declared", expr.line)
            return symbol.type

        if isinstance(expr, UnaryExpr):
            if expr.operator != "-":
                self._error(f"unsupported unary operator '{expr.operator}'", expr.line)
            if self._is_int_literal(expr) and isinstance(expected_type, FloatType):
                return FloatType()
            operand_type = self.check_expression(expr.operand)
            if isinstance(operand_type, (IntType, FloatType, MatrixType)):
                return operand_type
            self._error(f"unary '-' is not defined for {operand_type}", expr.line)

        if isinstance(expr, BinaryExpr):
            return self._check_binary(expr)

        if isinstance(expr, MatrixLiteralExpr):
            return self._check_matrix_literal(expr)

        if isinstance(expr, MatrixAccessExpr):
            symbol = self.symbol_table.lookup(expr.matrix_name)
            if symbol is None:
                self._error(f"'{expr.matrix_name}' is not declared", expr.line)
            self._expect_matrix(symbol.type, expr.line, f"'{expr.matrix_name}' indexing")
            self._check_matrix_indices(
                symbol.type, expr.row_index, expr.column_index, expr.line
            )
            return FloatType()

        if isinstance(expr, TransposeExpr):
            operand_type = self.check_expression(expr.operand)
            self._expect_matrix(operand_type, expr.line, "transpose")
            return MatrixType(operand_type.cols, operand_type.rows)

        if isinstance(expr, CallExpr):
            return self._check_builtin_call(expr)

        self._error(
            f"unsupported expression node {type(expr).__name__}",
            getattr(expr, "line", 1),
        )

    def _check_builtin_call(self, expr):
        name = expr.function_name
        args = expr.arguments or []
        arities = {
            "rows": 1,
            "cols": 1,
            "determinant": 1,
            "inverse": 1,
            "toFloat": 1,
            "toInt": 1,
        }
        if name not in arities:
            self._error(f"unknown built-in function '{name}'", expr.line)
        expected_arity = arities[name]
        if len(args) != expected_arity:
            self._error(
                f"built-in '{name}' expects {expected_arity} argument(s), got {len(args)}",
                expr.line,
            )

        arg_type = self.check_expression(args[0])
        if name in ("rows", "cols"):
            self._expect_matrix(arg_type, expr.line, f"built-in '{name}'")
            return IntType()

        if name == "determinant":
            self._expect_matrix(arg_type, expr.line, "built-in 'determinant'")
            if not arg_type.is_square():
                self._error(
                    f"built-in 'determinant' requires a square matrix, got {arg_type}",
                    expr.line,
                )
            return FloatType()

        if name == "inverse":
            self._expect_matrix(arg_type, expr.line, "built-in 'inverse'")
            if not arg_type.is_square():
                self._error(
                    f"built-in 'inverse' requires a square matrix, got {arg_type}",
                    expr.line,
                )
            return arg_type

        # Conversion built-ins accept scalar numeric values only.
        if not isinstance(arg_type, (IntType, FloatType)):
            self._error(
                f"built-in '{name}' requires a scalar numeric argument, got {arg_type}",
                expr.line,
            )
        return FloatType() if name == "toFloat" else IntType()

    def _check_binary(self, expr):
        left_expr = expr.left_operand
        right_expr = expr.right_operand
        left_type = self.check_expression(left_expr)
        right_type = self.check_expression(right_expr)
        op = expr.operator

        if op in ("+", "-"):
            if isinstance(left_type, (IntType, FloatType)) and left_type == right_type:
                return left_type
            if isinstance(left_type, MatrixType) and isinstance(right_type, MatrixType):
                if left_type != right_type:
                    self._error(
                        f"matrix operator '{op}' requires equal dimensions, "
                        f"got {left_type} and {right_type}",
                        expr.line,
                    )
                return left_type
            self._error(
                f"operator '{op}' requires matching operand types, "
                f"got {left_type} and {right_type}",
                expr.line,
            )

        if op == "*":
            if isinstance(left_type, (IntType, FloatType)) and left_type == right_type:
                return left_type
            if isinstance(left_type, MatrixType) and isinstance(right_type, MatrixType):
                if left_type.cols != right_type.rows:
                    self._error(
                        "matrix multiplication requires left columns to equal "
                        f"right rows, got {left_type} and {right_type}",
                        expr.line,
                    )
                return MatrixType(left_type.rows, right_type.cols)
            if isinstance(left_type, MatrixType) and isinstance(right_type, FloatType):
                return left_type
            if isinstance(left_type, FloatType) and isinstance(right_type, MatrixType):
                return right_type
            if isinstance(left_type, MatrixType) and self._is_int_literal(right_expr):
                return left_type
            if self._is_int_literal(left_expr) and isinstance(right_type, MatrixType):
                return right_type
            self._error(
                f"operator '*' is not defined for {left_type} and {right_type}",
                expr.line,
            )

        if op == "/":
            if isinstance(left_type, (IntType, FloatType)) and left_type == right_type:
                return left_type
            if isinstance(left_type, MatrixType) and isinstance(right_type, FloatType):
                return left_type
            if isinstance(left_type, MatrixType) and self._is_int_literal(right_expr):
                return left_type
            self._error(
                f"operator '/' is not defined for {left_type} and {right_type}",
                expr.line,
            )

        self._error(f"unknown binary operator '{op}'", expr.line)

    def _check_matrix_literal(self, expr):
        if not expr.rows or not expr.rows[0]:
            self._error("matrix literal must contain at least one row and column", expr.line)
        expected_cols = len(expr.rows[0])
        for row_number, row in enumerate(expr.rows, start=1):
            if len(row) != expected_cols:
                self._error(
                    f"matrix literal row {row_number} has {len(row)} element(s); "
                    f"expected {expected_cols}",
                    expr.line,
                )
            for element in row:
                actual = self.check_expression(
                    element,
                    expected_type=FloatType() if self._is_int_literal(element) else None,
                )
                if not isinstance(actual, FloatType):
                    self._error(
                        f"matrix elements must be float, got {actual}",
                        element.line,
                    )
        return MatrixType(len(expr.rows), expected_cols)

    def _check_assignment_value(self, value, expected, line, context):
        actual = self.check_expression(
            value,
            expected_type=expected if isinstance(expected, FloatType) else None,
        )
        self._expect_same(actual, expected, line, context)

    def check_statement(self, statement):
        if isinstance(statement, DeclarationStmt):
            declared_type = statement.declared_type
            if isinstance(declared_type, MatrixType) and not declared_type.has_valid_dimensions():
                self._error(
                    f"matrix declaration must have positive dimensions, got {declared_type}",
                    statement.line,
                )
            if statement.initializer is not None:
                self._check_assignment_value(
                    statement.initializer, declared_type, statement.line, "initializer"
                )
            self.symbol_table.declare(
                Symbol(statement.declared_identifier, declared_type, statement.line)
            )
            return

        if isinstance(statement, AssignmentStmt):
            if isinstance(statement.target, MatrixAccessExpr):
                symbol = self.symbol_table.lookup(statement.target.matrix_name)
                if symbol is None:
                    self._error(
                        f"'{statement.target.matrix_name}' is not declared",
                        statement.line,
                    )
                self._expect_matrix(
                    symbol.type, statement.line,
                    f"'{statement.target.matrix_name}' indexed assignment",
                )
                self._check_matrix_indices(
                    symbol.type,
                    statement.target.row_index,
                    statement.target.column_index,
                    statement.line,
                )
                self._check_assignment_value(
                    statement.value, FloatType(), statement.line, "indexed assignment"
                )
                return

            symbol = self.symbol_table.lookup(statement.target)
            if symbol is None:
                self._error(f"'{statement.target}' is not declared", statement.line)
            self._check_assignment_value(
                statement.value, symbol.type, statement.line, "assignment"
            )
            return

        if isinstance(statement, PrintStmt):
            for arg in statement.arguments:
                if isinstance(arg, LiteralExpr) and isinstance(arg.value, str):
                    continue
                self.check_expression(arg)
            return

        if isinstance(statement, IfStmt):
            self.check_expression(statement.condition, "if")
            self.check_statement(statement.then_branch)
            if statement.else_branch is not None:
                self.check_statement(statement.else_branch)
            return

        if isinstance(statement, WhileStmt):
            self.check_expression(statement.condition, "while")
            self.check_statement(statement.loop_body)
            return

        if isinstance(statement, BlockStmt):
            self.symbol_table.enter_scope()
            try:
                for inner in statement.statements:
                    self.check_statement(inner)
            finally:
                self.symbol_table.exit_scope()
            return

        self._error(
            f"unsupported statement node {type(statement).__name__}",
            getattr(statement, "line", 1),
        )


def check_program(program):
    return TypeChecker().check_program(program)