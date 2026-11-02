from src.lexer.token import TokenKind
from src.ast.ast_node import (DeclarationStmt, LiteralExpr, VariableExpr, UnaryExpr, AssignmentStmt, 
                              MatrixAccessExpr, BinaryExpr, CallExpr, TransposeExpr, MatrixLiteralExpr,
                              IfStmt, WhileStmt, BlockStmt, PrintStmt, Program)
from src.semantic.type import IntType, FloatType, MatrixType


class ParseError(Exception):
    def __init__(self, message, line):
        super().__init__(f"Syntax error on line {line}: {message}")
        self.message = message
        self.line = line


# Token kinds that can start a type.
TYPE_START_KINDS = (TokenKind.INT, TokenKind.FLOAT, TokenKind.MATRIX)

# Escape sequences the lexer accepts inside string literals (spec section 2.3).
_ESCAPES = {'"': '"', '\\': '\\', 'n': '\n', 't': '\t'}


def _unescape(raw):
    """Resolve \\" \\\\ \\n \\t in a string literal's text (quotes already removed)."""
    out = []
    i = 0
    while i < len(raw):
        if raw[i] == '\\' and i + 1 < len(raw):
            out.append(_ESCAPES.get(raw[i + 1], raw[i + 1]))
            i += 2
        else:
            out.append(raw[i])
            i += 1
    return ''.join(out)

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


    #Expressions parser 
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

    #Assignments
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

    # Statements and control flow
    def parse_statement(self):
        if self.is_type_start():
            return self.parse_declaration()

        if self.check(TokenKind.IDENTIFIERLIT):
            next_token = self.peek(1).kind

            if next_token in (
                TokenKind.ASSIGNMENT,
                TokenKind.LBRACKET
            ):
                return self.parse_assignment()

        return self.parse_embedded_stmt()

    def parse_embedded_stmt(self):
        """embedded_stmt -> assignment | print_stmt | if_stmt | while_stmt | block
        A declaration is NOT allowed here (spec 3.2)."""
        tok = self.peek()
        if tok.kind == TokenKind.IDENTIFIERLIT:
            return self.parse_assignment()
        if tok.kind == TokenKind.PRINT:
            return self.parse_print_stmt()
        if tok.kind == TokenKind.IF:
            return self.parse_if_stmt()
        if tok.kind == TokenKind.WHILE:
            return self.parse_while_stmt()
        if tok.kind == TokenKind.LCURLY:
            return self.parse_block()
        if self.is_type_start():
            raise ParseError("A declaration is not allowed here; put it inside a block { }",
                             tok.line)
        raise ParseError(f"Expected a statement (found '{tok.lexeme}')", tok.line)

    def parse_if_stmt(self):
        """if_stmt -> 'if' '(' expression ')' embedded_stmt ('else' embedded_stmt)?"""
        if_tok = self.expect(TokenKind.IF, "Expected 'if'")
        self.expect(TokenKind.LPAREN, "Expected '(' after 'if'")
        condition = self.parse_expression()
        self.expect(TokenKind.RPAREN, "Expected ')' after if condition")
        then_branch = self.parse_embedded_stmt()
        else_branch = None
        if self.match(TokenKind.ELSE):              # greedy: else binds to the nearest if
            else_branch = self.parse_embedded_stmt()
        return IfStmt(if_tok.line, condition, then_branch, else_branch)

    def parse_while_stmt(self):
        """while_stmt -> 'while' '(' expression ')' embedded_stmt"""
        while_tok = self.expect(TokenKind.WHILE, "Expected 'while'")
        self.expect(TokenKind.LPAREN, "Expected '(' after 'while'")
        condition = self.parse_expression()
        self.expect(TokenKind.RPAREN, "Expected ')' after while condition")
        body = self.parse_embedded_stmt()
        return WhileStmt(while_tok.line, condition, body)

    def parse_block(self):
        """block -> '{' statement* '}'"""
        start = self.expect(TokenKind.LCURLY, "Expected '{' to start block")
        statements = []
        while not self.check(TokenKind.RCURLY):
            if self.is_at_end():                    # otherwise an unclosed { never ends
                raise ParseError("Unterminated block: expected '}'", start.line)
            statements.append(self.parse_statement())
        self.expect(TokenKind.RCURLY, "Expected '}' to close block")
        return BlockStmt(start.line, statements)

    #successful parse of MatLang program statements
    def parse_print_stmt(self):
        """print_stmt -> 'print' '(' print_arg (',' print_arg)* ')' ';'"""
        print_tok = self.expect(TokenKind.PRINT, "Expected 'print'")
        self.expect(TokenKind.LPAREN, "Expected '(' after 'print'")
        arguments = [self.parse_print_arg()]
        while self.match(TokenKind.COMMA):
            arguments.append(self.parse_print_arg())
        self.expect(TokenKind.RPAREN, "Expected ')' after print arguments")
        self.expect(TokenKind.SEMICOLON, "Expected ';' after print statement")
        return PrintStmt(print_tok.line, arguments)

    def parse_print_arg(self):
        """print_arg -> STRING | expression"""
        tok = self.peek()
        if self.match(TokenKind.STRINGLIT):
            return LiteralExpr(tok.line, _unescape(tok.lexeme[1:-1]))  # drop the quotes
        return self.parse_expression()

    def parse_program(self):
        """program -> statement*  (must consume every token up to EOF)"""
        statements = []
        while not self.is_at_end():
            statements.append(self.parse_statement())
        return Program(statements)