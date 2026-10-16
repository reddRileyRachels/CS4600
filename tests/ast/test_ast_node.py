''' FOR TESTING nodes, use command:
python -m pytest tests/ast/test_ast_node.py
'''
#from src.ast.ast_node import ASTNode, Statement, Expression

#testIfStmt = nodes.IfStmt(line=6, condition="condition", then_branch="then", else_branch="else")
#print(testIfStmt.line, testIfStmt.condition, testIfStmt.then_branch, testIfStmt.else_branch)

from src.ast import ast_node as nodes

def test_program():
    test_program = nodes.Program(statements=["stmt1", "stmt2"], line=1)

    assert test_program.line == 1
    assert test_program.statements == ["stmt1", "stmt2"]


''' STATEMENTS '''


def test_if_statement():
    test_if = nodes.IfStmt(line=6, condition="condition", then_branch="then", else_branch="else")

    assert test_if.line == 6
    assert test_if.condition == "condition"
    assert test_if.then_branch == "then"
    assert test_if.else_branch == "else"

    print("test completed!")

def test_declaration_stmt():
    test_declare = nodes.DeclarationStmt(line=2, declared_type=int, declared_identifier="x")

    assert test_declare.line == 2
    assert test_declare.declared_type == int
    assert test_declare.declared_identifier == "x"

def test_assignment_stmt():
    test_assignment = nodes.AssignmentStmt(line=3, target="y", value=6)

    assert test_assignment.line == 3
    assert test_assignment.target == "y"
    assert test_assignment.value == 6

def test_while_stmt():
    test_while = nodes.WhileStmt(line=5, condition="condition", loop_body="loop_body")

    assert test_while.line == 5
    assert test_while.condition == "condition"
    assert test_while.loop_body == "loop_body"

def test_print_stmt():
    test_print = nodes.PrintStmt(line=7, arguments=["arg1", "arg2"])

    assert test_print.line == 7
    assert test_print.arguments == ["arg1", "arg2"]

def test_block_stmt():
    test_block = nodes.BlockStmt(line=4, statements=["statement1", "statement2"])

    assert test_block.line == 4
    assert test_block.statements == ["statement1", "statement2"]


''' EXPRESSIONS '''
def test_literal_expr():
    test_literal = nodes.LiteralExpr(line=8, value=42)

    assert test_literal.line == 8
    assert test_literal.value == 42

def test_variable_expr():
    test_variable = nodes.VariableExpr(line=9, identifier="dragon")

    assert test_variable.line == 9
    assert test_variable.identifier == "dragon"

def test_unary_expr():
    test_unary = nodes.UnaryExpr(line=10, operand="12", operator="-")

    assert test_unary.line == 10
    assert test_unary.operand == "12"
    assert test_unary.operator == "-"

def test_binary_expr():
    test_binary = nodes.BinaryExpr(line=11, left="23", operator="+", right="5")

    assert test_binary.line == 11
    assert test_binary.left_operand == "23"
    assert test_binary.operator == "+"
    assert test_binary.right_operand == "5"

def test_call_expr():
    test_call = nodes.CallExpr(line=12, function_name="dragon_fly", arguments=["start_pos", "end_pos"])

    assert test_call.line == 12
    assert test_call.function_name == "dragon_fly"
    assert test_call.arguments == ["start_pos", "end_pos"]

def test_matrix_access_expr():
    test_matrix_access = nodes.MatrixAccessExpr(line=13, matrix_name="matrix_of_dragons", row_index=2, column_index=3)

    assert test_matrix_access.line == 13
    assert test_matrix_access.matrix_name == "matrix_of_dragons"
    assert test_matrix_access.row_index == 2
    assert test_matrix_access.column_index == 3

def test_matrix_literal_expr():
    test_matrix_literal = nodes.MatrixLiteralExpr(line=14, rows=[[1.0, 2.0], [3.0, 4.0]])

    assert test_matrix_literal.line == 14
    assert test_matrix_literal.rows == [[1.0, 2.0], [3.0, 4.0]]

def test_transpose_expr():
    test_transpose = nodes.TransposeExpr(line=15, operand="matrix_of_dragons")

    assert test_transpose.line == 15
    assert test_transpose.operand == "matrix_of_dragons"