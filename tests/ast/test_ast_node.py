#from src.ast.ast_node import ASTNode, Statement, Expression

#testIfStmt = nodes.IfStmt(line=6, condition="condition", then_branch="then", else_branch="else")
#print(testIfStmt.line, testIfStmt.condition, testIfStmt.then_branch, testIfStmt.else_branch)

from src.ast import ast_node as nodes

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

