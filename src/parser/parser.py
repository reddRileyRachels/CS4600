from src.lexer.token import TokenKind
from src.ast.ast_node import (DeclarationStmt, LiteralExpr, VariableExpr, UnaryExpr, AssignmentStmt, 
                              MatrixAccessExpr, BinaryExpr, CallExpr, TransposeExpr, MatrixLiteralExpr)
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


    #Expression parser 
    def parse_expression(self):
        """expression -> additive"""
        return self.parse_additive()

    def parse_additive(self):
        """additive -> multiplicative (('+' | '-') multiplicative)*"""
        node = self.parse_multiplicative()
        while self.peek().kind in (TokenKind.SUM, TokenKind.DIFFERENCE):
            op = self.advance()
            right = self.parse_multiplicative()
            node = BinaryExpr(op.line, node, op.lexeme, right)   # old node becomes left child
        return node

    def parse_multiplicative(self):
        """multiplicative -> unary (('*' | '/') unary)*"""
        node = self.parse_unary()
        while self.peek().kind in (TokenKind.PRODUCT, TokenKind.QUOTIENT):
            op = self.advance()
            right = self.parse_unary()
            node = BinaryExpr(op.line, node, op.lexeme, right)
        return node

    def parse_unary(self):
        """unary -> '-' unary | postfix"""
        if self.peek().kind == TokenKind.DIFFERENCE:
            op = self.advance()
            return UnaryExpr(op.line, self.parse_unary(), op.lexeme)
        return self.parse_postfix()

    def parse_postfix(self):
        """postfix -> primary "'"*"""
        node = self.parse_primary()
        while self.peek().kind == TokenKind.TRANSPOSE:
            op = self.advance()
            node = TransposeExpr(op.line, node)
        return node

    def parse_primary(self):
        """primary -> INTLIT | FLOATLIT | IDENTIFIER
                    | IDENTIFIER '(' arg_list ')'
                    | IDENTIFIER '[' expression ',' expression ']'
                    | matrix_literal | '(' expression ')'"""
        tok = self.peek()

        if self.match(TokenKind.INTLIT):
            return LiteralExpr(tok.line, int(tok.lexeme))
        if self.match(TokenKind.FLOATLIT):
            return LiteralExpr(tok.line, float(tok.lexeme))

        if self.match(TokenKind.IDENTIFIERLIT):
            if self.match(TokenKind.LPAREN):                       # call
                args = self.parse_arg_list()
                self.expect(TokenKind.RPAREN, "Expected ')' after function arguments")
                return CallExpr(tok.line, tok.lexeme, args)
            if self.match(TokenKind.LBRACKET):                     # index
                row = self.parse_expression()
                self.expect(TokenKind.COMMA, "Expected ',' between matrix indices")
                col = self.parse_expression()
                self.expect(TokenKind.RBRACKET, "Expected ']' after matrix indices")
                return MatrixAccessExpr(tok.line, tok.lexeme, row, col)
            return VariableExpr(tok.line, tok.lexeme)

        if tok.kind == TokenKind.LBRACKET:
            return self.parse_matrix_literal()

        if self.match(TokenKind.LPAREN):
            node = self.parse_expression()
            self.expect(TokenKind.RPAREN, "Expected ')' to close parenthesized expression")
            return node                                            # parens leave no node

        raise ParseError(f"Expected an expression (found '{tok.lexeme}')", tok.line)

    def parse_arg_list(self):
        """arg_list -> expression (',' expression)*"""
        args = [self.parse_expression()]
        while self.match(TokenKind.COMMA):
            args.append(self.parse_expression())
        return args

    def parse_matrix_literal(self):
        """matrix_literal -> '[' row (';' row)* ']'"""
        start = self.expect(TokenKind.LBRACKET, "Expected '[' to start matrix literal")
        rows = [self.parse_row()]
        while self.match(TokenKind.SEMICOLON):
            rows.append(self.parse_row())
        self.expect(TokenKind.RBRACKET, "Expected ']' to close matrix literal")
        return MatrixLiteralExpr(start.line, rows)

    def parse_row(self):
        """row -> expression (',' expression)*"""
        row = [self.parse_expression()]
        while self.match(TokenKind.COMMA):
            row.append(self.parse_expression())
        return row
    
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