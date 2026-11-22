import pytest
from src.lexer.lexer import lexer
from src.lexer.token import TokenKind


def test_keywords():
    tokens = lexer("int float if else")

    expected = [
        (TokenKind.INT, "int"),
        (TokenKind.FLOAT, "float"),
        (TokenKind.IF, "if"),
        (TokenKind.ELSE, "else"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_identifiers():
    tokens = lexer("x total _temp A1 matrix2")

    expected = [
        (TokenKind.IDENTIFIERLIT, "x"),
        (TokenKind.IDENTIFIERLIT, "total"),
        (TokenKind.IDENTIFIERLIT, "_temp"),
        (TokenKind.IDENTIFIERLIT, "A1"),
        (TokenKind.IDENTIFIERLIT, "matrix2"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_operators():
    tokens = lexer("+ - * / ' =")

    expected = [
        (TokenKind.SUM, "+"),
        (TokenKind.DIFFERENCE, "-"),
        (TokenKind.PRODUCT, "*"),
        (TokenKind.QUOTIENT, "/"),
        (TokenKind.TRANSPOSE, "'"),
        (TokenKind.ASSIGNMENT, "="),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_punctuation():
    tokens = lexer("( ) { } [ ] < > , ;")

    expected = [
        (TokenKind.LPAREN, "("),
        (TokenKind.RPAREN, ")"),
        (TokenKind.LCURLY, "{"),
        (TokenKind.RCURLY, "}"),
        (TokenKind.LBRACKET, "["),
        (TokenKind.RBRACKET, "]"),
        (TokenKind.LESSTHAN, "<"),
        (TokenKind.GREATERTHAN, ">"),
        (TokenKind.COMMA, ","),
        (TokenKind.SEMICOLON, ";"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_integer_literals():
    tokens = lexer("0 1 42 1000")

    expected = [
        (TokenKind.INTLIT, "0"),
        (TokenKind.INTLIT, "1"),
        (TokenKind.INTLIT, "42"),
        (TokenKind.INTLIT, "1000"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_float_literals():
    tokens = lexer("3.14 0.5 6.02e23 1e10 1.5e-10")

    expected = [
        (TokenKind.FLOATLIT, "3.14"),
        (TokenKind.FLOATLIT, "0.5"),
        (TokenKind.FLOATLIT, "6.02e23"),
        (TokenKind.FLOATLIT, "1e10"),
        (TokenKind.FLOATLIT, "1.5e-10"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_negative_number():
    tokens = lexer("-5 -3.14")

    expected = [
        (TokenKind.DIFFERENCE, "-"),
        (TokenKind.INTLIT, "5"),
        (TokenKind.DIFFERENCE, "-"),
        (TokenKind.FLOATLIT, "3.14"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_longest_match():
    tokens = lexer("1e10 integer whileLoop")

    expected = [
        (TokenKind.FLOATLIT, "1e10"),
        (TokenKind.IDENTIFIERLIT, "integer"),
        (TokenKind.IDENTIFIERLIT, "whileLoop"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_strings():
    tokens = lexer('"hello" "say \\"hi\\"" "line\\nbreak"')

    expected = [
        (TokenKind.STRINGLIT, '"hello"'),
        (TokenKind.STRINGLIT, '"say \\"hi\\""'),
        (TokenKind.STRINGLIT, '"line\\nbreak"'),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_whitespace():
    tokens = lexer("  int\t x\r\n ; ")

    expected = [
        (TokenKind.INT, "int"),
        (TokenKind.IDENTIFIERLIT, "x"),
        (TokenKind.SEMICOLON, ";"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_line_comment():
    tokens = lexer("int x; // comment\nfloat y;")

    expected = [
        (TokenKind.INT, "int"),
        (TokenKind.IDENTIFIERLIT, "x"),
        (TokenKind.SEMICOLON, ";"),
        (TokenKind.FLOAT, "float"),
        (TokenKind.IDENTIFIERLIT, "y"),
        (TokenKind.SEMICOLON, ";"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_block_comment():
    tokens = lexer("int /* comment */ x;")

    expected = [
        (TokenKind.INT, "int"),
        (TokenKind.IDENTIFIERLIT, "x"),
        (TokenKind.SEMICOLON, ";"),
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_empty_input():
    tokens = lexer("")

    expected = [
        (TokenKind.EOF, ""),
    ]

    actual = [(t.kind, t.lexeme) for t in tokens]

    assert actual == expected


def test_invalid_character():
    with pytest.raises(SyntaxError, match="Lexical error"):
        lexer("int x = 10 @ 20;")


def test_malformed_number():
    with pytest.raises(SyntaxError, match="Lexical error"):
        lexer("1.2.3")


def test_unterminated_string():
    with pytest.raises(SyntaxError, match="Lexical error"):
        lexer('"hello')


def test_unterminated_comment():
    with pytest.raises(SyntaxError, match="unterminated block comment"):
        lexer("int x; /* unfinished")


def test_line_numbers():
    tokens = lexer("int x;\nfloat y;")

    expected = [
        (TokenKind.INT, "int", 1),
        (TokenKind.IDENTIFIERLIT, "x", 1),
        (TokenKind.SEMICOLON, ";", 1),
        (TokenKind.FLOAT, "float", 2),
        (TokenKind.IDENTIFIERLIT, "y", 2),
        (TokenKind.SEMICOLON, ";", 2),
        (TokenKind.EOF, "", 2),
    ]

    actual = [(t.kind, t.lexeme, t.line) for t in tokens]

    assert actual == expected
