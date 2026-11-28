import pytest
from src.generator.generator import Generator
from src.ast import ast_node as nodes
from src.parser.parser import Parser
from src.lexer.lexer import lexer

def expr(source):
    """Lex `source` and parse it as a single expression."""
    return Parser(lexer(source)).parse_expression()

def literal(value):
    return nodes.LiteralExpr(1, value)

def variable(name):
    return nodes.VariableExpr(1, name)

def unary(operator, operand):
    return nodes.UnaryExpr(1, operand, operator)

def binary(left, operator, right):
    return nodes.BinaryExpr(1, left, operator, right)

def test_generate_literal():
    generator = Generator()
    assert generator.generate_expression(literal(5)) == "5"

def test_generate_variable():
    generator = Generator()
    assert generator.generate_expression(variable("x")) == "x"

@pytest.mark.parametrize("operator, value, expected", [
    ("-", 5, "-5"),
])
def test_generate_unary(operator, value, expected):
    generator = Generator()
    expression = unary(operator, literal(value))
    assert generator.generate_expression(expression) == expected

@pytest.mark.parametrize("operator, expected", [
    ("+", "(5 + 3)"),
    ("-", "(5 - 3)"),
    ("*", "(5 * 3)"),
])
def test_generate_binary_operators(operator, expected):
    generator = Generator()
    expression = binary(literal(5), operator, literal(3))
    assert generator.generate_expression(expression) == expected

def test_generate_integer_division():
    generator = Generator()
    expression = binary(literal(5), "/", literal(3))
    assert generator.generate_expression(expression) == "((abs(5) // abs(3)) * (1 if (5) * (3) >= 0 else -1))"

def test_generate_integer_division_negative_result():
    generator = Generator()
    expression = binary(literal(-5), "/", literal(3))
    assert generator.generate_expression(expression) == "((abs(-5) // abs(3)) * (1 if (-5) * (3) >= 0 else -1))"

def test_generate_integer_division_negative_operands():
    generator = Generator()
    expression = binary(literal(-5), "/", literal(-3))
    assert generator.generate_expression(expression) == "((abs(-5) // abs(-3)) * (1 if (-5) * (-3) >= 0 else -1))"

def test_generate_float_division():
    generator = Generator()
    expression = binary(literal(5.0), "/", literal(3.0))
    assert generator.generate_expression(expression) == "(5.0 / 3.0)"

def test_generate_binary_with_variables():
    generator = Generator()
    expression = binary(variable("x"), "+", variable("y"))
    assert generator.generate_expression(expression) == "(x + y)"

def test_generate_declaration():
    generator = Generator()
    node = nodes.DeclarationStmt(1, "int", "x", literal(5))
    generator.generate_declaration(node)
    assert generator.output == ["x = 5"]
    assert generator.variable_types == {"x": "int"}

def test_generate_assignment():
    generator = Generator()
    node = nodes.AssignmentStmt(1, "x", literal(10))
    generator.generate_assignment(node)
    assert generator.output == ["x = 10"]

def test_generate_print():
    generator = Generator()
    node = nodes.PrintStmt(1, [literal(5), variable("x")])
    generator.generate_print(node)
    assert generator.output == ['print(5, x, sep="")']

def test_generate_if():
    generator = Generator()
    node = nodes.IfStmt(
        1,
        literal(True),
        nodes.BlockStmt(1, [nodes.PrintStmt(1, [literal(1)])])
    )
    generator.generate_if(node)
    assert generator.output == [
        "if True:",
        '\tprint(1, sep="")'
    ]

def test_generate_if_else():
    generator = Generator()
    node = nodes.IfStmt(
        1,
        literal(True),
        nodes.BlockStmt(1, [nodes.PrintStmt(1, [literal(1)])]),
        nodes.BlockStmt(1, [nodes.PrintStmt(1, [literal(2)])])
    )
    generator.generate_if(node)
    assert generator.output == [
        "if True:",
        '\tprint(1, sep="")',
        "else:",
        '\tprint(2, sep="")'
    ]

def test_generate_empty_if():
    generator = Generator()
    node = nodes.IfStmt(
        1,
        literal(True),
        nodes.BlockStmt(1, [])
    )
    generator.generate_if(node)
    assert generator.output == [
        "if True:",
        "\tpass"
    ]

def test_generate_empty_if_else():
    generator = Generator()
    node = nodes.IfStmt(
        1,
        literal(True),
        nodes.BlockStmt(1, []),
        nodes.BlockStmt(1, [])
    )
    generator.generate_if(node)
    assert generator.output == [
        "if True:",
        "\tpass",
        "else:",
        "\tpass"
    ]

def test_generate_empty_while():
    generator = Generator()
    node = nodes.WhileStmt(
        1,
        literal(True),
        nodes.BlockStmt(1, [])
    )
    generator.generate_while(node)
    assert generator.output == [
        "while True:",
        "\tpass"
    ]

def test_generate_while():
    generator = Generator()
    node = nodes.WhileStmt(
        1,
        literal(True),
        nodes.BlockStmt(1, [nodes.PrintStmt(1, [literal(1)])])
    )
    generator.generate_while(node)
    assert generator.output == [
        "while True:",
        '\tprint(1, sep="")'
    ]

def test_generate_block():
    generator = Generator()
    node = nodes.BlockStmt(1, [
        nodes.AssignmentStmt(1, "x", literal(1)),
        nodes.PrintStmt(1, [variable("x")])
    ])
    generator.generate_block(node)
    assert generator.output == [
        "x = 1",
        'print(x, sep="")'
    ]

def test_increase_indent():
    generator = Generator()
    generator.increase_indent()
    assert generator.indent_level == 1

def test_decrease_indent():
    generator = Generator()
    generator.indent_level = 2
    generator.decrease_indent()
    assert generator.indent_level == 1

def test_decrease_indent_does_not_go_below_zero():
    generator = Generator()
    generator.decrease_indent()
    assert generator.indent_level == 0

def test_emit_line():
    generator = Generator()
    generator.indent_level = 2
    generator.emit_line("print(5)")
    assert generator.output == ["\t\tprint(5)"]

def test_generate_program():
    generator = Generator()
    program = nodes.Program([
        nodes.DeclarationStmt(1, "int", "x", literal(5)),
        nodes.PrintStmt(1, [variable("x")])
    ])
    result = generator.generate(program)
    assert result == 'x = 5\nprint(x, sep="")'

def test_generate_print_string():
    generator = Generator()
    node = nodes.PrintStmt(1, [literal("Hello")])
    generator.generate_print(node)
    assert generator.output == ['print(\'Hello\', sep="")']

def test_generate_string_literal():
    generator = Generator()
    assert generator.generate_expression(literal("Hello")) == "'Hello'"

def test_get_expression_type_integer_literal():
    generator = Generator()
    assert generator.get_expression_type(literal(5)) == "int"

def test_get_expression_type_float_literal():
    generator = Generator()
    assert generator.get_expression_type(literal(5.0)) == "float"

def test_get_expression_type_string_literal():
    generator = Generator()
    assert generator.get_expression_type(literal("Hello")) == "string"

def test_get_expression_type_boolean_literal():
    generator = Generator()
    assert generator.get_expression_type(literal(True)) == "bool"

def test_get_expression_type_declared_variable():
    generator = Generator()
    generator.generate_declaration(
        nodes.DeclarationStmt(1, "int", "x", literal(5))
    )
    assert generator.get_expression_type(variable("x")) == "int"

def test_get_expression_type_integer_binary():
    generator = Generator()
    expression = binary(literal(5), "+", literal(3))
    assert generator.get_expression_type(expression) == "int"

def test_get_expression_type_float_binary():
    generator = Generator()
    expression = binary(literal(5.0), "+", literal(3))
    assert generator.get_expression_type(expression) == "float"

def test_get_expression_type_integer_division():
    generator = Generator()
    expression = binary(literal(5), "/", literal(3))
    assert generator.get_expression_type(expression) == "int"

def test_get_expression_type_float_division():
    generator = Generator()
    expression = binary(literal(5.0), "/", literal(3))
    assert generator.get_expression_type(expression) == "float"

def test_generate_resets_state():
    generator = Generator()
    program = nodes.Program([
        nodes.DeclarationStmt(1, "int", "x", literal(5))
    ])
    generator.generate(program)

    second_program = nodes.Program([
        nodes.PrintStmt(1, [literal(10)])
    ])
    result = generator.generate(second_program)

    assert result == 'print(10, sep="")'
    assert generator.variable_types == {}
    assert generator.indent_level == 0

@pytest.mark.parametrize("left, right, expected", [
    (5, 3, 1),
    (-5, 3, -1),
    (5, -3, -1),
    (-5, -3, 1),
])
def test_integer_division_runtime(left, right, expected):
    generator = Generator()
    expression = binary(literal(left), "/", literal(right))
    generated = generator.generate_expression(expression)
    assert eval(generated) == expected


def test_matrix_declaration_copy():
    source = """
    matrix<2,2> A;
    matrix<2,2> B = A;
    """

    program = Parser(lexer(source)).parse_program()

    generator = Generator()
    output = generator.generate(program)

    assert "B = (A).copy()" in output


def test_generate_matrix_assignment_copy():
    generator = Generator()
    source = """
    matrix<2,2> A;
    matrix<2,2> B;
    B = A;
    """

    program = Parser(lexer(source)).parse_program()

    output = generator.generate(program)

    assert "B = (A).copy()" in output

def test_scalar_assignment_does_not_copy():
    source = """
    int A = 5;
    int B;
    B = A;
    """

    program = Parser(lexer(source)).parse_program()

    generator = Generator()
    output = generator.generate(program)

    assert "B = A" in output
    assert "B = (A).copy()" not in output

def test_uninitialized_variable_generates_none():
    source = "int x;"
    program = Parser(lexer(source)).parse_program()
    generator = Generator()
    output = generator.generate(program)
    assert output == "x = None"

def test_uninitialized_matrix_generates_none():
    source = "matrix<2,2> A;"
    program = Parser(lexer(source)).parse_program()
    generator = Generator()
    output = generator.generate(program)
    assert output == "A = None"

def test_matrix_declaration_copy_binary_expression():
    source = """
    matrix<2,2> A;
    matrix<2,2> B;
    matrix<2,2> C = A + B;
    """
    program = Parser(lexer(source)).parse_program()
    generator = Generator()
    output = generator.generate(program)
    assert "C = ((A + B)).copy()" in output

def test_matrix_assignment_copy_binary_expression():
    source = """
    matrix<2,2> A;
    matrix<2,2> B;
    matrix<2,2> C;
    C = A + B;
    """
    program = Parser(lexer(source)).parse_program()
    generator = Generator()
    output = generator.generate(program)
    assert "C = ((A + B)).copy()" in output

def test_generate_matrix_literal_2x2():
    node = expr("[1; 2; 3; 4]")