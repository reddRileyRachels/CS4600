from src.ast import ast_node as nodes
from src.semantic.type import MatrixType

class Generator:
    def __init__(self):
        self.output = []
        self.indent_level = 0
        self.variable_types = {}

    def generate(self, program):
        self.output = []
        self.indent_level = 0
        self.variable_types = {}

        for statement in program.statements:
            self.generate_statement(statement)

        return "\n".join(self.output)

    def generate_statement(self, statement):
        if isinstance(statement, nodes.DeclarationStmt):
            self.generate_declaration(statement)
        elif isinstance(statement, nodes.AssignmentStmt):
            self.generate_assignment(statement)
        elif isinstance(statement, nodes.PrintStmt):
            self.generate_print(statement)
        elif isinstance(statement, nodes.IfStmt):
            self.generate_if(statement)
        elif isinstance(statement, nodes.WhileStmt):
            self.generate_while(statement)
        elif isinstance(statement, nodes.BlockStmt):
            self.generate_block(statement)

    def generate_expression(self, expression):
        if isinstance(expression, nodes.LiteralExpr):
            return self.generate_literal(expression)
        elif isinstance(expression, nodes.VariableExpr):
            return self.generate_variable(expression)
        elif isinstance(expression, nodes.UnaryExpr):
            return self.generate_unary(expression)
        elif isinstance(expression, nodes.BinaryExpr):
            return self.generate_binary(expression)
        elif isinstance(expression, nodes.MatrixLiteralExpr):
            return self.generate_matrix_literal(expression)
        elif isinstance(expression, nodes.MatrixAccessExpr):
            return self.generate_matrix_access(expression)

    def emit_line(self, code):
        self.output += ["\t" * self.indent_level + code]

    def increase_indent(self):
        self.indent_level += 1

    def decrease_indent(self):
        if self.indent_level >= 1:
            self.indent_level -= 1
        else:
            self.indent_level = 0

    def generate_declaration(self, node):
        identifier = node.declared_identifier
        self.variable_types[identifier] = node.declared_type

        if node.initializer is not None:
            initializer = self.generate_expression(node.initializer)
            if isinstance(self.variable_types[identifier], MatrixType):
                initializer = (f"({initializer}).copy()")
            
            self.emit_line(f"{identifier} = {initializer}")

        else:
            self.emit_line(f"{identifier} = None")

    def generate_assignment(self, node):
        target = node.target
        value = self.generate_expression(node.value)

        if isinstance(target, str) and isinstance(
            self.variable_types.get(target), MatrixType
        ):
            value = (f"({value}).copy()")

        self.emit_line(f"{target} = {value}")

    def generate_print(self, node):
        arguments = node.arguments
        arguments_list = []

        for argument in arguments:
            generated = self.generate_expression(argument)
            arguments_list += [generated]

        arguments_string = ", ".join(arguments_list)
        self.emit_line(f'print({arguments_string}, sep="")')

    def generate_if(self, node):
        condition = self.generate_expression(node.condition)

        self.emit_line(f"if {condition}:")
        self.increase_indent()

        previous_output_length = len(self.output)
        self.generate_statement(node.then_branch)

        if len(self.output) == previous_output_length:
            self.emit_line("pass")

        self.decrease_indent()

        if node.else_branch is not None:
            self.emit_line("else:")
            self.increase_indent()

            previous_output_length = len(self.output)
            self.generate_statement(node.else_branch)

            if len(self.output) == previous_output_length:
                self.emit_line("pass")

            self.decrease_indent()

    def generate_while(self, node):
        condition = self.generate_expression(node.condition)

        self.emit_line(f"while {condition}:")
        self.increase_indent()

        previous_output_length = len(self.output)
        self.generate_statement(node.loop_body)

        if len(self.output) == previous_output_length:
            self.emit_line("pass")

        self.decrease_indent()

    def generate_block(self, node):
        statements = node.statements

        for statement in statements:
            self.generate_statement(statement)

    def generate_literal(self, node):
        if isinstance(node.value, str):
            return repr(node.value)

        return str(node.value)

    def generate_variable(self, node):
        return str(node.identifier)

    def generate_unary(self, node):
        operator = node.operator
        operand = self.generate_expression(node.operand)
        return f"{operator}{operand}"

    def generate_binary(self, node):
        left = self.generate_expression(node.left_operand)
        operator = node.operator
        right = self.generate_expression(node.right_operand)

        if operator == "/":
            left_type = self.get_expression_type(node.left_operand)
            right_type = self.get_expression_type(node.right_operand)

            if left_type == "int" and right_type == "int":
                return f"((abs({left}) // abs({right})) * (1 if ({left}) * ({right}) >= 0 else -1))"

            return f"({left} / {right})"

        return f"({left} {operator} {right})"

    def get_expression_type(self, expression):
        if isinstance(expression, nodes.LiteralExpr):
            if isinstance(expression.value, bool):
                return "bool"
            elif isinstance(expression.value, int):
                return "int"
            elif isinstance(expression.value, float):
                return "float"
            elif isinstance(expression.value, str):
                return "string"

        elif isinstance(expression, nodes.VariableExpr):
            return self.variable_types.get(expression.identifier)

        elif isinstance(expression, nodes.UnaryExpr):
            return self.get_expression_type(expression.operand)

        elif isinstance(expression, nodes.BinaryExpr):
            left_type = self.get_expression_type(expression.left_operand)
            right_type = self.get_expression_type(expression.right_operand)

            if expression.operator == "/":
                if left_type == "int" and right_type == "int":
                    return "int"
                return "float"

            if left_type == "float" or right_type == "float":
                return "float"

            if left_type == "int" and right_type == "int":
                return "int"

        return None

    def generate_matrix_literal(self, node):
        rows = []
        for row in node.rows:
            elements = [
                self.generate_expression(element)
                for element in row
            ]
            rows.append(f"[{', '.join(elements)}]")
        return f"np.array([{', '.join(rows)}], dtype=float)"

    def generate_matrix_access(self, node):
        matrix = node.matrix_name
        row = self.generate_expression(node.row_index)
        column = self.generate_expression(node.column_index)
        return f"{matrix}[({row}) - 1, ({column}) - 1]"