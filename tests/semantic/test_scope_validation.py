"""CS-26: does the symbol table validate scope boundaries, declarations and shadowing
on REAL MatLang programs?  (spec sections 2.5, 5.1, 5.6, 7)

test_symbol_table.py tests Scope / SymbolTable on their own. This file runs whole
programs through the real lexer and parser, then walks the AST with a small
scope-checking harness that drives the symbol table the way the semantic
analyzer will:

    BlockStmt        -> enter_scope(), check the statements, exit_scope()
    DeclarationStmt  -> check the initializer FIRST, then declare() the name
    VariableExpr     -> lookup()  (None means 'undeclared')
    AssignmentStmt   -> lookup() the target (plain name or M[i, j])
    CallExpr         -> function names are built-ins, NOT looked up; only the arguments are

The harness only checks NAMES (scope rules). Types are not checked here; that is
the type checker's job. See test-docs/symbol_table_scopes.md.
"""

import pytest

from src.lexer.lexer import lexer
from src.parser.parser import Parser
from src.ast.ast_node import (
    Program, DeclarationStmt, AssignmentStmt, PrintStmt, IfStmt, WhileStmt, BlockStmt,
    LiteralExpr, VariableExpr, UnaryExpr, BinaryExpr, CallExpr, MatrixAccessExpr,
    MatrixLiteralExpr, TransposeExpr,
)
from src.semantic.symbol import Symbol
from src.semantic.symbol_table import SymbolTable, SemanticError
from src.semantic.type import IntType, FloatType


# --- scope-checking harness ---------------------------------------------------

class ScopeChecker:
    """Walks an AST and applies the spec 5.1 scope rules using SymbolTable."""

    def __init__(self):
        self.table = SymbolTable()

    def check_program(self, program):
        for stmt in program.statements:
            self.check_statement(stmt)

    def check_statement(self, stmt):
        if isinstance(stmt, DeclarationStmt):
            # The initializer is checked BEFORE the name is declared, so
            # `int x = x;` is "x used before its declaration", and in
            # `{ int x = x + 1; }` the right-hand x is the OUTER x.
            if stmt.initializer is not None:
                self.check_expression(stmt.initializer)
            self.table.declare(Symbol(stmt.declared_identifier, stmt.declared_type, stmt.line))
        elif isinstance(stmt, AssignmentStmt):
            if isinstance(stmt.target, MatrixAccessExpr):
                self.check_expression(stmt.target)
            else:
                self.require_declared(stmt.target, stmt.line)
            self.check_expression(stmt.value)
        elif isinstance(stmt, PrintStmt):
            for arg in stmt.arguments:
                self.check_expression(arg)
        elif isinstance(stmt, IfStmt):
            self.check_expression(stmt.condition)
            self.check_statement(stmt.then_branch)
            if stmt.else_branch is not None:
                self.check_statement(stmt.else_branch)
        elif isinstance(stmt, WhileStmt):
            self.check_expression(stmt.condition)
            self.check_statement(stmt.loop_body)
        elif isinstance(stmt, BlockStmt):
            self.table.enter_scope()
            for inner in stmt.statements:
                self.check_statement(inner)
            self.table.exit_scope()
        else:
            raise TypeError(f"Unknown statement node {type(stmt).__name__}")

    def check_expression(self, expr):
        if isinstance(expr, LiteralExpr):
            return                                   # numbers and print strings
        if isinstance(expr, VariableExpr):
            self.require_declared(expr.identifier, expr.line)
        elif isinstance(expr, MatrixAccessExpr):
            self.require_declared(expr.matrix_name, expr.line)
            self.check_expression(expr.row_index)
            self.check_expression(expr.column_index)
        elif isinstance(expr, CallExpr):
            for arg in expr.arguments or []:         # the function name itself is a built-in
                self.check_expression(arg)
        elif isinstance(expr, BinaryExpr):
            self.check_expression(expr.left_operand)
            self.check_expression(expr.right_operand)
        elif isinstance(expr, (UnaryExpr, TransposeExpr)):
            self.check_expression(expr.operand)
        elif isinstance(expr, MatrixLiteralExpr):
            for row in expr.rows:
                for element in row:
                    self.check_expression(element)
        else:
            raise TypeError(f"Unknown expression node {type(expr).__name__}")

    def require_declared(self, name, line):
        if self.table.lookup(name) is None:
            raise SemanticError(f"'{name}' is not declared", line)


def check(source):
    """Lex, parse and scope-check a MatLang program. Returns the checker."""
    program = Parser(lexer(source)).parse_program()
    assert isinstance(program, Program)
    checker = ScopeChecker()
    checker.check_program(program)
    return checker


def assert_scope_error(source, line=None):
    """The program must parse, but be rejected by the scope rules."""
    with pytest.raises(SemanticError) as err:
        check(source)
    if line is not None:
        assert err.value.line == line
    return err.value


# --- spec section 8 example programs (must all pass) ---------------------------

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
def test_spec_example_programs_pass(source):
    check(source)


def test_spec_8_2_block_names_do_not_leak():
    # A_inv, x and check live only inside the if-block
    checker = check(SPEC_8_2)
    for name in ("A_inv", "x", "check"):
        assert checker.table.lookup(name) is None
    assert checker.table.lookup("det") is not None


def test_scopes_are_balanced_after_program():
    checker = check(SPEC_8_2)
    assert checker.table.current_scope is checker.table.global_scope


# --- variable declarations -------------------------------------------------------

def test_declared_variable_can_be_used():
    check("int x = 1; print(x);")


def test_declaration_without_initializer_can_be_assigned():
    check("int x; x = 3; print(x);")


def test_undeclared_variable_is_error():
    # spec 7 example: `z = 1;` with no z
    assert_scope_error("z = 1;", line=1)


def test_use_before_declaration_is_error():
    assert_scope_error("print(x);\nint x = 1;", line=1)


def test_initializer_cannot_use_its_own_name():
    # the name is visible only FROM its declaration (spec 5.1)
    assert_scope_error("int x = x;")


def test_redeclaration_in_same_scope_is_error():
    assert_scope_error("int x = 1;\nfloat x = 2.0;", line=2)


def test_redeclaration_in_same_block_is_error():
    assert_scope_error("{\n int y = 1;\n int y = 2;\n}", line=3)


@pytest.mark.parametrize("name", ["rows", "cols", "determinant", "inverse", "toFloat", "toInt"])
def test_declaring_builtin_name_is_error(name):
    # spec 2.5
    assert_scope_error(f"int {name} = 1;")


def test_calling_builtin_needs_no_declaration():
    check("matrix<2, 2> A = [1, 2; 3, 4]; float d = determinant(A); int r = rows(A);")


# --- scope boundaries ------------------------------------------------------------

def test_block_sees_outer_variable():
    check("int x = 1; { x = 2; print(x); }")


def test_deeply_nested_block_sees_outermost_variable():
    check("int x = 1; { { { print(x); } } }")


def test_variable_not_visible_after_its_block():
    assert_scope_error("{ int y = 1; }\nprint(y);", line=2)


def test_if_block_variable_not_visible_in_else_block():
    assert_scope_error("int c = 1;\nif (c) { int t = 1; } else { print(t); }")


def test_while_body_variable_not_visible_after_loop():
    assert_scope_error("int n = 2;\nwhile (n) { int k = n; n = n - 1; }\nprint(k);", line=3)


def test_while_body_declaration_is_fine_each_time():
    # the body is one block scope; declaring inside it is legal
    check("int n = 3; while (n) { int k = n; n = n - 1; }")


def test_sibling_blocks_can_reuse_a_name():
    check("{ int t = 1; } { float t = 2.0; }")


def test_if_and_else_blocks_can_reuse_a_name():
    check("int c = 1; if (c) { int t = 1; } else { int t = 2; }")


def test_undeclared_name_in_condition_is_error():
    assert_scope_error("if (flag) { print(1); }")


def test_undeclared_name_inside_matrix_literal_is_error():
    assert_scope_error("matrix<1, 2> A = [1.0, w];")


def test_undeclared_name_in_index_is_error():
    assert_scope_error("matrix<2, 2> A = [1, 2; 3, 4]; float e = A[i, 1];")


def test_undeclared_matrix_in_index_assignment_is_error():
    assert_scope_error("B[1, 1] = 2.0;")


def test_undeclared_name_in_builtin_argument_is_error():
    assert_scope_error("float d = determinant(Q);")


# --- shadowing ------------------------------------------------------------------

def test_shadowing_in_block_is_legal():
    check("int x = 1; { float x = 2.0; print(x); }")


def test_shadow_uses_inner_symbol():
    # Step through `int x = 1; { float x = 2.0; }` by hand to look inside the block.
    program = Parser(lexer("int x = 1; { float x = 2.0; }")).parse_program()
    checker = ScopeChecker()
    checker.check_statement(program.statements[0])               # int x = 1;
    checker.table.enter_scope()                                  # {
    checker.check_statement(program.statements[1].statements[0]) # float x = 2.0;
    assert isinstance(checker.table.lookup("x").type, FloatType) # inner x wins
    checker.table.exit_scope()                                   # }
    assert isinstance(checker.table.lookup("x").type, IntType)   # outer x is back


def test_outer_variable_restored_after_shadow_block():
    checker = check("int x = 1; { float x = 2.0; }")
    assert checker.table.lookup("x").line == 1


def test_shadow_initializer_refers_to_outer_variable():
    # in the inner declaration, the right-hand x is still the OUTER x
    check("int x = 1; { int x = x + 1; }")


def test_shadowing_in_nested_blocks():
    check("int x = 1; { float x = 2.0; { int x = 3; print(x); } print(x); } print(x);")


def test_redeclare_after_shadow_in_same_block_is_error():
    assert_scope_error("int x = 1;\n{\n float x = 2.0;\n int x = 3;\n}", line=4)


# --- error reporting --------------------------------------------------------------

def test_error_message_names_the_variable():
    err = assert_scope_error("int a = 1;\nprint(b);")
    assert "'b'" in str(err)
    assert "line 2" in str(err)
