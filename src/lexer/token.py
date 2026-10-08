class TokenKind:
    # Keywords
    INT = "INT"
    FLOAT = "FLOAT"
    MATRIX = "MATRIX"
    IF = "IF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    PRINT = "PRINT"

    # Operators
    SUM = "SUM"
    DIFFERENCE = "DIFFERENCE"
    PRODUCT = "PRODUCT"
    QUOTIENT = "QUOTIENT"
    TRANSPOSE = "TRANSPOSE"
    ASSIGNMENT = "ASSIGNMENT"

    # Punctuation/Grouping
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LCURLY = "LCURLY"
    RCURLY = "RCURLY"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    LESSTHAN = "LESSTHAN"
    GREATERTHAN = "GREATERTHAN"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"

    # Literals
    INTLIT = "INTLIT"
    FLOATLIT = "FLOATLIT"
    STRINGLIT = "STRINGLIT"
    IDENTIFIERLIT = "IDENTIFIERLIT"

    EOF = "EOF"


class Token:
    def __init__(self, kind, lexeme, line):
        self.kind = kind
        self.lexeme = lexeme
        self.line = line
