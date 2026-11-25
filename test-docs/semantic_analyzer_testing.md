# Semantic Analyzer Testing (CS-30)

## Purpose and scope

This document records how the MatLang semantic analyzer (`src/semantic/type_checker.py`) was tested against the language specification (MatlangSpec v2.0). The goal of the ticket was to confirm that the analyzer rejects every **static type, dimension, and scope error** the spec defines, and accepts valid programs (including all four spec §8 example programs).

The analyzer does not check the three run-time errors (spec §6), and lexical and syntax errors belong to earlier phases. See "Phase boundaries" and "Known gaps and handoff".

## How to run

From the repository root:

    pytest tests/semantic/

**Result: 391 passed, 0 failed.**

## Test files

| File | Covers |
|---|---|
| `test_type.py` | Type equality, `matrix<1,1>` is not `float`, scalar/matrix classification, dimension validity (§4.1, §4.2) |
| `test_symbol_table.py` | Scopes, redeclaration, shadowing, reserved built-in names (§2.5, §5.1) |
| `test_scope_validation.py` | Scope rules on real parsed programs using a scope-only harness (§5.1) |
| `test_type_checker.py` | Scalar operators, context-typed integer literals (§4.3, §5.2) |
| `test_semantic_matrix_assignment_builtins.py` | Matrix dimensions, assignments, built-in functions (§5.2, §5.6, §5.7) |
| `test_semantic_errors.py` | Conditions, indexing, division, unary minus, transpose, conversions, scope rules through `TypeChecker`, spec §8 programs |

Note: `test_scope_validation.py` uses its own `ScopeChecker` and does not call `TypeChecker`. To confirm the real analyzer enforces scope rules, `test_semantic_errors.py` repeats the key scope cases through `TypeChecker`.

## Coverage by error class

### Type errors

| Spec rule | Example rejected | Test file |
|---|---|---|
| §5.2 no `int` + `float` (either order) | `int x = 1; float y = 2.0; int z = x + y;` | `test_type_checker.py` |
| §5.2 `int * float` | `int a; float b; float c = a * b;` | `test_semantic_errors.py` |
| §5.6 assignment types must be equal | `int x = 3.5;`, `float y = x` (int `x`) | `test_type_checker.py` |
| §4.3 literals do not propagate through arithmetic | `float x = 3 / 2;`, `x = 3 + 0;` | `test_type_checker.py` |
| §4.3 rule 1 (matrix literal elements) | `[n]` with int `n`, `[1 + 2]` rejected; `[1,2;3,4]`, `[-1,2]` accepted | `test_type_checker.py` |
| §4.3 rule 2 (matrix × / ÷ scalar) | `A * n`, `A * (1 + 1)` rejected; `A * 2`, `2 * A`, `A / 2` accepted | `test_type_checker.py` |
| §4.3 rule 3 (float target) | `float x = 3;` and `float x = -3;` accepted | `test_type_checker.py` |
| §5.2 no broadcasting | `A + 2.0` | `test_type_checker.py` |
| §5.2 division rules | `2.0 / A`, `A / A`, `A / n` (int variable) | `test_semantic_errors.py` |
| §4.1 `matrix<1,1>` is not a scalar | `float x = A;` with `matrix<1,1> A` | `test_semantic_errors.py` |
| §5.3 unary minus on int, float, matrix | accepted for all three | `test_semantic_errors.py` |
| §5.4 transpose | scalar rejected; `A'` swaps dimensions; `A''` keeps type; `-A'` | `test_semantic_errors.py` |
| §5.5 index types | `A[1.0, 1]` rejected; indexing a scalar rejected | `test_semantic_errors.py` |
| §5.5 indexed assignment value must be float | `A[1,1] = A;`, `A[1,1] = n` (int variable) rejected; literal `3` accepted | `test_semantic_matrix_assignment_