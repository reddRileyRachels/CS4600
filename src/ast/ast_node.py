# defines different node types based on the MatlangSpec.pdf grammar rules
# defines statements then expressions
class ASTNode:
    def __init__(self, line):
        self.line = line

class Statement(ASTNode):
    pass

class Expression(ASTNode):
    pass

class Program(ASTNode):
    def __init__(self, statement_list, line="None"):
        super().__init__(line) # a program may or may not have a corresponding line
        self.statement_list = statement_list # program is defined as zero or more statements

class DeclarationStmt(Statement):
    def __init__(self, line, declared_type, declared_identifier, initializer="None"):
        super().__init__(line)
        self.declared_type = declared_type # int, float, etc.
        self.declared_identifier = declared_identifier # name of variable
        self.initializer = initializer # initializer is optional: int x versus int x = 6; both are valid

class AssignmentStmt(Statement):
    def __init__(self, line, identifier, value):
        super().__init__(line)
        self.identifier = identifier 
        self.value = value # value is an expression

class PrintStmt(Statement):
    def __init__(self, line, arguments):
        super().__init__(line)
        self.arguments = arguments

class IfStmt(Statement):
    def __init__(self, line, condition, then_branch, else_branch="None"):
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
    def __init__(self, line, block_code):
        super().__init__(line)
        self.block_code = block_code # the code inside blocks is any number of statements