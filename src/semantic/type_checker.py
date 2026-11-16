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
    WhileStmt)
from src.semantic.symbol import Symbol
from src.semantic.symbol_table import SemanticError, SymbolTable
from src.semantic.type import FloatType, IntType, MatrixType


class TypeChecker:
    def __init__(self, symbol_table=None):
        self.symbol_table = symbol_table if symbol_table is not None else SymbolTable()

    def _error(self, message, line):
        raise SemanticError(message, line if line is not None else 1)

    @staticmethod
    def _is_int_literal(expr):
        if isinstance(expr, LiteralExpr):
            return type(expr.value) is int
        return (
            isinstance(expr, UnaryExpr)
            and expr.operator == "-"
            and isinstance(expr.operand, LiteralExpr)
            and type(expr.operand.value) is int
        )

    def _expect_same(self, actual, expected, line, context):
        if actual != expected:
            self._error(f"{context} requires {expected}, got {actual}", line)

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
            if not isinstance(symbol.type, MatrixType):
                self._error(f"'{expr.matrix_name}' is not a matrix", expr.line)
            return FloatType()

        if isinstance(expr, TransposeExpr):
            operand_type = self.check_expression(expr.operand)
            if not isinstance(operand_type, MatrixType):
                self._error("transpose requires a matrix operand", expr.line)
            return MatrixType(operand_type.cols, operand_type.rows)

        if isinstance(expr, CallExpr):
            return_types = {
                "rows": IntType,
                "cols": IntType,
                "determinant": FloatType,
                "inverse": None,
                "toFloat": FloatType,
                "toInt": IntType,
            }
            if expr.function_name == "inverse":
                args = expr.arguments or []
                if args and isinstance(args[0], VariableExpr):
                    symbol = self.symbol_table.lookup(args[0].identifier)
                    if symbol is not None and isinstance(symbol.type, MatrixType):
                        return symbol.type
                return MatrixType(1, 1)
            result_type = return_types.get(expr.function_name)
            if result_type is not None:
                return result_type()
            self._error(f"cannot determine type of function '{expr.function_name}'", expr.line)

        self._error(f"unsupported expression node {type(expr).__name__}", getattr(expr, "line", 1))

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
                # Shape compatibility is handled by the separate matrix-dimension checks.
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
                # Matrix shape compatibility is intentionally not checked here.
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
        for row in expr.rows:
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
        rows = len(expr.rows)
        cols = len(expr.rows[0]) if expr.rows else 0
        return MatrixType(rows, cols)

    def check_statement(self, statement):
        if isinstance(statement, DeclarationStmt):
            declared_type = statement.declared_type
            if statement.initializer is not None:
                actual = self.check_expression(
                    statement.initializer,
                    expected_type=(
                        declared_type
                        if isinstance(declared_type, FloatType)
                        else None
                    ),
                )
                if not (
                    isinstance(declared_type, MatrixType)
                    and isinstance(statement.initializer, MatrixLiteralExpr)
                ):
                    self._expect_same(
                        actual,
                        declared_type,
                        statement.line,
                        "initializer",
                    )
            self.symbol_table.declare(
                Symbol(statement.declared_identifier, declared_type, statement.line)
            )
            return

        if isinstance(statement, AssignmentStmt):
            if isinstance(statement.target, MatrixAccessExpr):
                actual = self.check_expression(
                    statement.value,
                    expected_type=FloatType(),
                )
                self._expect_same(
                    actual,
                    FloatType(),
                    statement.line,
                    "indexed assignment",
                )
                return

            symbol = self.symbol_table.lookup(statement.target)
            if symbol is None:
                self._error(
                    f"'{statement.target}' is not declared",
                    statement.line,
                )
            expected = symbol.type
            actual = self.check_expression(
                statement.value,
                expected_type=(
                    expected if isinstance(expected, FloatType) else None
                ),
            )
            if not (
                isinstance(expected, MatrixType)
                and isinstance(statement.value, MatrixLiteralExpr)
            ):
                self._expect_same(
                    actual,
                    expected,
                    statement.line,
                    "assignment",
                )
            return

        if isinstance(statement, PrintStmt):
            for arg in statement.arguments:
                if isinstance(arg, LiteralExpr) and isinstance(arg.value, str):
                    continue
                self.check_expression(arg)
            return

        if isinstance(statement, IfStmt):
            self.check_expression(statement.condition)
            self.check_statement(statement.then_branch)
            if statement.else_branch is not None:
                self.check_statement(statement.else_branch)
            return

        if isinstance(statement, WhileStmt):
            self.check_expression(statement.condition)
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
