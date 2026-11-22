import re
from src.lexer.token import Token, TokenKind

KEYWORDS = {
    "int": TokenKind.INT,
    "float": TokenKind.FLOAT,
    "matrix": TokenKind.MATRIX,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
    "print": TokenKind.PRINT,
}


TOKEN_PATTERNS = [
    # Operators
    ("SUM", r"\+"),
    ("DIFFERENCE", r"-"),
    ("PRODUCT", r"\*"),
    ("QUOTIENT", r"/"),
    ("TRANSPOSE", r"'"),
    ("ASSIGNMENT", r"="),
    # Punctuation/Grouping
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LCURLY", r"\{"),
    ("RCURLY", r"\}"),
    ("LBRACKET", r"\["),
    ("RBRACKET", r"\]"),
    ("LESSTHAN", r"<"),
    ("GREATERTHAN", r">"),
    ("COMMA", r","),
    ("SEMICOLON", r";"),
    # Literals
    ("STRINGLIT", r'"([^"\\\n]|\\["\\nt])*"'),
    ("FLOATLIT", r"(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"),
    ("INTLIT", r"[0-9]+"),
    ("IDENTIFIERLIT", r"[A-Za-z_][A-Za-z0-9_]*"),
]


TOKEN_KINDS = {
    "SUM": TokenKind.SUM,
    "DIFFERENCE": TokenKind.DIFFERENCE,
    "PRODUCT": TokenKind.PRODUCT,
    "QUOTIENT": TokenKind.QUOTIENT,
    "TRANSPOSE": TokenKind.TRANSPOSE,
    "ASSIGNMENT": TokenKind.ASSIGNMENT,
    "LPAREN": TokenKind.LPAREN,
    "RPAREN": TokenKind.RPAREN,
    "LCURLY": TokenKind.LCURLY,
    "RCURLY": TokenKind.RCURLY,
    "LBRACKET": TokenKind.LBRACKET,
    "RBRACKET": TokenKind.RBRACKET,
    "LESSTHAN": TokenKind.LESSTHAN,
    "GREATERTHAN": TokenKind.GREATERTHAN,
    "COMMA": TokenKind.COMMA,
    "SEMICOLON": TokenKind.SEMICOLON,
    "INTLIT": TokenKind.INTLIT,
    "FLOATLIT": TokenKind.FLOATLIT,
    "STRINGLIT": TokenKind.STRINGLIT,
    "IDENTIFIERLIT": TokenKind.IDENTIFIERLIT,
}

COMPILED_PATTERNS = [(name, re.compile(pattern)) for name, pattern in TOKEN_PATTERNS]

WHITESPACE_RE = re.compile(r"[ \t\r\n]+")
INTEGER_RE = re.compile(r"[0-9]+")
FLOAT_RE = re.compile(
    r"(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|" r"[0-9]+[eE][+-]?[0-9]+)"
)


def lexer(code):

    for index, char in enumerate(code):
        if ord(char) > 127:
            line = code.count("\n", 0, index) + 1
            raise SyntaxError(
                f"Lexical error at line {line}: " f"non-ASCII character {char!r}"
            )

    tokens = []
    position = 0
    line = 1
    length = len(code)

    while position < length:

        whitespace = WHITESPACE_RE.match(code, position)
        if whitespace:
            lexeme = whitespace.group(0)
            line += lexeme.count("\n")
            position = whitespace.end()
            continue

        if code.startswith("//", position):
            end = code.find("\n", position)

            if end == -1:
                position = length
            else:
                position = end

            continue

        if code.startswith("/*", position):
            start_line = line
            end = code.find("*/", position + 2)

            if end == -1:
                raise SyntaxError(
                    f"Lexical error at line {start_line}: " "unterminated block comment"
                )

            comment = code[position : end + 2]
            line += comment.count("\n")
            position = end + 2
            continue

        if code[position].isdigit():
            malformed_decimal = re.match(r"[0-9]+\.(?![0-9])", code[position:])

            if malformed_decimal:
                raise SyntaxError(
                    f"Lexical error at line {line}: malformed numeric literal"
                )

            first_float = FLOAT_RE.match(code, position)

            if first_float:
                after_float = first_float.end()

                if after_float < length and code[after_float] == ".":
                    raise SyntaxError(
                        f"Lexical error at line {line}: malformed numeric literal"
                    )

        best_name = None
        best_lexeme = ""

        for name, pattern in COMPILED_PATTERNS:
            match = pattern.match(code, position)

            if match:
                lexeme = match.group(0)

                if len(lexeme) > len(best_lexeme):
                    best_name = name
                    best_lexeme = lexeme

        if best_name is None:
            raise SyntaxError(
                f"Lexical error at line {line}: "
                f"unexpected character {code[position]!r}"
            )

        name = best_name
        lexeme = best_lexeme

        if name in ("INTLIT", "FLOATLIT"):
            end_position = position + len(lexeme)
            following = code[end_position:]

            if (
                following.startswith(".")
                and len(following) > 1
                and following[1].isdigit()
            ):
                raise SyntaxError(
                    f"Lexical error at line {line}: " "malformed numeric literal"
                )

        if code[position] == '"' and name != "STRINGLIT":
            raise SyntaxError(
                f"Lexical error at line {line}: "
                "unterminated string or invalid escape"
            )

        if name == "IDENTIFIERLIT":
            kind = KEYWORDS.get(lexeme, TokenKind.IDENTIFIERLIT)
        else:
            kind = TOKEN_KINDS[name]

        tokens.append(Token(kind, lexeme, line))
        position += len(lexeme)

    tokens.append(Token(TokenKind.EOF, "", line))

    return tokens
