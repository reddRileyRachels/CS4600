BUILTIN_NAMES = frozenset({"rows", "cols", "determinant", "inverse", "toFloat", "toInt"})


class SemanticError(Exception):
    def __init__(self, message, line):
        super().__init__(f"Semantic error on line {line}: {message}")
        self.message = message
        self.line = line


class Scope:
    def __init__(self, parent=None):
        self.parent = parent      
        self.symbols = {}         


    def define(self, symbol):

        self.symbols[symbol.name] = symbol

    def resolve_local(self, name):
        return self.symbols.get(name)

    def resolve(self, name):
        scope = self
        while scope is not None:
            symbol = scope.resolve_local(name)
            if symbol is not None:
                return symbol
            scope = scope.parent
        return None


class SymbolTable:
    def __init__(self):
        self.global_scope = Scope()           
        self.current_scope = self.global_scope

    def enter_scope(self):
        self.current_scope = Scope(parent=self.current_scope)

    def exit_scope(self):
        if self.current_scope.parent is None:
            raise RuntimeError("Cannot exit the program scope")
        self.current_scope = self.current_scope.parent

    def declare(self, symbol):
        if symbol.name in BUILTIN_NAMES:
            raise SemanticError(
                f"'{symbol.name}' is a reserved built-in name and cannot be declared",
                symbol.line,
            )
        existing = self.lookup_current(symbol.name)
        if existing is not None:
            raise SemanticError(
                f"'{symbol.name}' is already declared in this scope (line {existing.line})",
                symbol.line,
            )
        self.current_scope.define(symbol)

    def lookup(self, name):
        return self.current_scope.resolve(name)

    def lookup_current(self, name):
        return self.current_scope.resolve_local(name)
