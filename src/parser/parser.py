from src.lexer.token import TokenKind
from src.ast.ast_node import DeclarationStmt, LiteralExpr, VariableExpr, UnaryExpr, AssignmentStmt, MatrixAccessExpr
from src.semantic.type import IntType, FloatType, MatrixType


class ParseError(Exception):
    def __init__(self, message, line):
        super().__init__(f"Syntax error on line {line}: {message}")
        self.message = message
        self.line = line


# Token kinds that can start a type.
TYPE_START_KINDS = (TokenKind.INT, TokenKind.FLOAT, TokenKind.MATRIX)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    # Token helpers
    def peek(self, offset=0):
        index = min(self.position + offset, len(self.tokens) - 1)
        return self.tokens[index]

    def previous(self):
        return self.tokens[self.position - 1]

    def is_at_end(self):
        return self.peek().kind == TokenKind.EOF

    def advance(self):
        if not self.is_at_end():
            self.position += 1
        return self.previous()

    def check(self, kind):
        return self.peek().kind == kind

    def match(self, *kinds):
        if self.peek().kind in kinds:
            self.advance()
            return True
        return False

    def expect(self, kind, message):
        if self.check(kind):
            return self.advance()
        raise ParseError(f"{message} (found '{self.peek().lexeme}')", self.peek().line)


    # Declarations and types
    def is_type_start(self):
        return self.peek().kind in TYPE_START_KINDS

    def parse_type(self):
        """type -> 'int' | 'float' | 'matrix' '<' INTEGER ',' INTEGER '>'

        Returns an IntType, FloatType, or MatrixType.
        """
        if self.match(TokenKind.INT):
            return IntType()
        if self.match(TokenKind.FLOAT):
            return FloatType()
        if self.match(TokenKind.MATRIX):
            self.expect(TokenKind.LESSTHAN, "Expected '<' after 'matrix'")
            rows = self.expect(TokenKind.INTLIT, "Expected integer row count in matrix type")
            self.expect(TokenKind.COMMA, "Expected ',' between matrix dimensions")
            cols = self.expect(TokenKind.INTLIT, "Expected integer column count in matrix type")
            self.expect(TokenKind.GREATERTHAN, "Expected '>' to close matrix type")
            return MatrixType(int(rows.lexeme), int(cols.lexeme))
        raise ParseError(
            f"Expected a type ('int', 'float' or 'matrix') (found '{self.peek().lexeme}')",
            self.peek().line,
        )

    def parse_declaration(self):
        """declaration -> type IDENTIFIER ( '=' expression )? ';'

        Returns a DeclarationStmt. declared_identifier is the variable name
        as a string; initializer is None for `int x;`.
        """
        line = self.peek().line
        declared_type = self.parse_type()
        name = self.expect(TokenKind.IDENTIFIERLIT, "Expected variable name after type")

        initializer = None
        if self.match(TokenKind.ASSIGNMENT):
            initializer = self.parse_expression()

        self.expect(TokenKind.SEMICOLON, "Expected ';' after declaration")
        return DeclarationStmt(line, declared_type, name.lexeme, initializer)


    # TEMPORARY expression parser (Claude suggested me to add it)
    def parse_expression(self):
        """TEMPORARY: only integer/float literals, variables, and unary minus.

        This stub lets the statement routines be built and tested now. Replace it with the full
        additive -> multiplicative -> unary -> postfix -> primary chain
        (spec section 3) when that ticket is done.
        """
        token = self.peek()
        if self.match(TokenKind.DIFFERENCE):
            return UnaryExpr(token.line, self.parse_expression(), token.lexeme)
        if self.match(TokenKind.INTLIT):
            return LiteralExpr(token.line, int(token.lexeme))
        if self.match(TokenKind.FLOATLIT):
            return LiteralExpr(token.line, float(token.lexeme))
        if self.match(TokenKind.IDENTIFIERLIT):
            return VariableExpr(token.line, token.lexeme)
        raise ParseError(f"Expected an expression (found '{token.lexeme}')", token.line)
        #this is maria- asked claude more info, it seems this also needs a "(" as an expression 

    
    def parse_assignment(self):
        """assignment -> IDENTIFIERLIT ASSIGNMENT expression SEMICOLON
                   | IDENTIFIERLIT LBRACKET expression COMMA expression RBRACKET
                     ASSIGNMENT expression SEMICOLON"""
        name_tok = self.expect(TokenKind.IDENTIFIERLIT, "Expected variable name")
        target = name_tok.lexeme                    # simple form: target is the name

        if self.match(TokenKind.LBRACKET):          # indexed form: M[i, j] = e;
            row = self.parse_expression()
            self.expect(TokenKind.COMMA, "Expected ',' between matrix indices")
            col = self.parse_expression()
            self.expect(TokenKind.RBRACKET, "Expected ']' after matrix indices")
            target = MatrixAccessExpr(name_tok.line, name_tok.lexeme, row, col)

        self.expect(TokenKind.ASSIGNMENT, "Expected '=' in assignment")
        value = self.parse_expression()
        self.expect(TokenKind.SEMICOLON, "Expected ';' after assignment")
        return AssignmentStmt(line=name_tok.line, target=target, value=value)