### Test Objectives:
__________________________________________
    * Symbol table validates scope boundaries
    * Symbol table validates variable declarations
    * Symbol table handles shadowing correctly
    * All rules follow MatLang spec sections 2.5 and 5.1 (and the semantic examples in section 7)

### Test Summary:
__________________________________________
    * Two test files, both in tests/semantic/:
        - test_symbol_table.py (30 tests): unit tests of Scope and SymbolTable on their own
          (declare, lookup, lookup_current, enter_scope, exit_scope)
        - test_scope_validation.py (40 tests): REAL MatLang programs go through the real lexer
          and parser, then a scope-checking harness walks the AST and drives the symbol table
          the way the semantic analyzer will
    * Result: all 70 tests pass (284 for the whole project)
    * The 4 example programs from spec section 8 all pass the scope check
    * The tests were checked by breaking the symbol table on purpose (mutation check).
      Every broken rule made tests fail:
        - redeclaration check removed      -> 3 tests fail
        - outward (parent) lookup removed   -> 10 tests fail
        - built-in name check removed       -> 6 tests fail
        - exit_scope does nothing           -> 6 tests fail

### How the scope harness works (test_scope_validation.py):
__________________________________________
    * BlockStmt { }      -> enter_scope(), check each statement, exit_scope()
    * DeclarationStmt    -> check the initializer FIRST, then declare() the name
    * VariableExpr       -> lookup(); None means "not declared" -> SemanticError
    * AssignmentStmt     -> lookup() the target (x = ... or M[i, j] = ...)
    * CallExpr           -> function names are built-ins and are NOT looked up; only arguments are
    * It checks names only. Types are not checked here; that is the type checker's job.

### Verifying Objectives:
___________________________________________
### Scope boundaries
    * Every { } block opens a new scope; the program is the outermost scope
        - A block sees variables from all enclosing scopes, even 3 blocks deep
        - A variable declared in a block is gone after the block closes
        - A variable from an if-block is not visible in the else-block
        - A variable from a while body is not visible after the loop
        - Two sibling blocks (or if/else blocks) can each declare the same name
        - After a whole program, the table is back at the global scope (balanced enter/exit)
        - In spec example 8.2, A_inv, x and check exist only inside the if-block

### Variable declarations
    * Declared variables can be used; declarations without an initializer can be assigned later
    * Errors detected (all with the correct line number):
        - Using an undeclared name: z = 1; (spec section 7 example)
        - Using a name before its declaration: print(x); int x = 1;
        - Using a name in its own initializer: int x = x;
        - Redeclaring a name in the same scope, or in the same block
        - Declaring any of the 6 built-in names: rows, cols, determinant, inverse, toFloat, toInt
        - Undeclared names inside conditions, matrix literals, indices, index assignments
          and built-in arguments
    * Calling a built-in (rows(A), determinant(A)) does NOT require a declaration

### Shadowing
    * Declaring a name in an inner block that exists outside is legal
        - Inside the block, lookup finds the inner variable (e.g. float x)
        - After the block, the outer variable is back (e.g. int x from line 1)
        - In { int x = x + 1; } the right-hand x is the OUTER x (initializer checked before declaring)
        - Shadowing works across several nesting levels
        - Redeclaring a name twice inside the same inner block is still an error

### Findings: missing work (new tickets)
__________________________________________
    * The symbol table itself works. It is NOT yet used by the compiler:
      no semantic analyzer walks the AST and calls it.

    1. NEW TICKET - Implement SemanticAnalyzer scope pass
        - Walk the AST and drive SymbolTable exactly like the harness in test_scope_validation.py
        - Rules found while testing that the analyzer must follow:
            * Check a declaration's initializer BEFORE declaring the name
              (otherwise int x = x; is accepted, and { int x = x + 1; } reads the wrong x)
            * Do not look up function names in calls; they are built-ins, not variables
            * Skip string literals in print arguments
        - When it exists, test_scope_validation.py can switch from the harness to the real analyzer

    2. NEW TICKET - Reject matrix dimensions below 1 (spec 4.1)
        - matrix<0, 2> A; currently passes the lexer, parser and scope check; nothing rejects it
        - The parser must keep accepting it (it is a semantic rule, not syntax)
        - The analyzer should call MatrixType.has_valid_dimensions() on every declared matrix type

    3. NEW TICKET (small) - Fill empty test placeholders
        - tests/semantic/test_symbol.py and tests/lexer/test_token.py are empty files
