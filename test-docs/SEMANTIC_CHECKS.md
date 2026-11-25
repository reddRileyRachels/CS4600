# Semantic checks added

The semantic analyzer now validates the following rules in `src/semantic/type_checker.py`.

## Matrix dimensions

- Matrix addition and subtraction require identical row and column counts.
- Matrix multiplication requires `left.cols == right.rows`; its result type is
  `matrix<left.rows,right.cols>`.
- Matrix declarations must have positive dimensions.
- Matrix literals must be non-empty and rectangular.
- Matrix initializers and assignments must match the declared matrix shape exactly.
- Matrix indexing and indexed assignment require a matrix target and integer
  row/column expressions. Literal indices are checked at compile time using
  indexing starts at 1. Non-literal indices are type-checked, but their run-time
  values cannot be proven in bounds by this static checker.

## Built-in functions

The checker validates the built-ins already listed by this project:

| Built-in | Arguments | Return type / rule |
|---|---|---|
| `rows(M)` | one matrix | `int` |
| `cols(M)` | one matrix | `int` |
| `determinant(M)` | one square matrix | `float` |
| `inverse(M)` | one square matrix | same matrix dimensions |
| `toFloat(int)` | | `float` |
| `toInt(float)` | | `int` |

Unknown function names, extra arguments, invalid argument types, and
non-square arguments to `determinant` / `inverse` are rejected.

## Tests

`tests/test_semantic_matrix_assignment_builtins.py` contains 23 positive and
negative tests covering the rules above. Run from the repository root:

```bash
python -m pytest -q
```

Result when run against this uploaded source snapshot: **23 passed**.

## Scope / limitations

The uploaded ZIP contained `src/` but not the repository's `MatlangSpec.pdf`,
existing `tests/`, or project configuration. Therefore, the built-in signatures
and zero-based interpretation of matrix indices above follow the interfaces
and conventions inferred from the supplied source, not an independently
verified copy of the language specification. The checker cannot statically
prove that a square matrix is invertible or determine the bounds of a
non-literal index expression.