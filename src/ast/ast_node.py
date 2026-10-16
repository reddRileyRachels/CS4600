''' defines different node types based on the MatlangSpec.pdf grammar rules '''
# defines statements then expressions
class ASTNode:
    def __init__(self, line):
        self.line = line

class Statement(ASTNode):
    pass

class Expression(ASTNode):
    pass

class Program(ASTNode):
    def __init__(self, statements, line=None):
        super().__init__(line) # a program may or may not have a corresponding line
        self.statements = statements # program is defined as zero or more statements

''' STATEMENTS '''
class DeclarationStmt(Statement):
    def __init__(self, line, declared_type, declared_identifier, initializer=None):
        super().__init__(line)
        self.declared_type = declared_type # int, float, etc.
        self.declared_identifier = declared_identifier # name of variable
        self.initializer = initializer # initializer is optional: int x versus int x = 6; both are valid

class AssignmentStmt(Statement):
    def __init__(self, line, target, value):
        super().__init__(line)
        self.target = target # target name; variable or matrix
        self.value = value # value is an expression

class PrintStmt(Statement):
    def __init__(self, line, arguments):
        super().__init__(line)
        self.arguments = arguments

class IfStmt(Statement):
    def __init__(self, line, condition, then_branch, else_branch=None):
        super().__init__(line)
        self.condition = condition
        self.then_branch = then_branch # branches may contain other statements
        self.else_branch = else_branch # else-branches are optional

class WhileStmt(Statement):
    def __init__(self, line, condition, loop_body):
        super().__init__(line)
        self.condition = condition
        self.loop_body = loop_body # some sort of embedded statement(s)

class BlockStmt(Statement):
    def __init__(self, line, statements):
        super().__init__(line)
        self.statements = statements # the statements inside the block


''' EXPRESSIONS '''
class LiteralExpr(Expression): # single literal value
    def __init__(self, line, value):
        super().__init__(line)
        self.value = value # value is a literal (int, float, etc.)

class VariableExpr(Expression): # single variable
    def __init__(self, line, identifier):
        super().__init__(line)
        self.identifier = identifier # identifier is target variable name

class UnaryExpr(Expression): # one operand and operator
    def __init__(self, line, operand, operator):
        super().__init__(line)
        self.operand = operand
        self.operator = operator 

class BinaryExpr(Expression): # operand, operator, operand
    def __init__(self, line, left, operator, right):
        super().__init__(line)
        self.left_operand = left
        self.operator = operator # +, -, *, /
        self.right_operand = right

class CallExpr(Expression): # function call
    def __init__(self, line, function_name, arguments=None):
        super().__init__(line)
        self.function_name = function_name
        self.arguments = arguments # optional; not all functions have parameters

class MatrixAccessExpr(Expression): # access target element in matrix
    def __init__(self, line, matrix_name, row_index, column_index):
        super().__init__(line)
        self.matrix_name = matrix_name
        self.row_index = row_index
        self.column_index = column_index

class MatrixLiteralExpr(Expression): # creating a "matrix" data type in inline code
    def __init__(self, line, rows):
        super().__init__(line)
        self.rows = rows # matrix values are a list of lists, each element being float (per MatLang spec)

class TransposeExpr(Expression): # transpose a matrix
    def __init__(self, line, operand):
        super().__init__(line)
        self.operand = operand