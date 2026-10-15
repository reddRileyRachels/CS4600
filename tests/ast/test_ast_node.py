''' FOR TESTING nodes, use command:
python -m pytest tests/ast/test_ast_node.py
'''
#from src.ast.ast_node import ASTNode, Statement, Expression

#testIfStmt = nodes.IfStmt(line=6, condition="condition", then_branch="then", else_branch="else")
#print(testIfStmt.line, testIfStmt.condition, testIfStmt.then_branch, testIfStmt.else_branch)

from src.ast import ast_node as nodes

def test_program():
    test_program = nodes.Program(statement_list=["stmt1", "stmt2"], line=1)

    assert test_program.line == 1
    assert test_program.statement_list == ["stmt1", "stmt2"]

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
    test_assignment = nodes.AssignmentStmt(line=3, identifier="y", value=6)

    assert test_assignment.line == 3
    assert test_assignment.identifier == "y"
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
    test_block = nodes.BlockStmt(line=4, block_code=["statement1", "statement2"])

    assert test_block.line == 4
    assert test_block.block_code == ["statement1", "statement2"]