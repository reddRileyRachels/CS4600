### Test Objectives:
__________________________________________
    * Parser passes unit tests
    * ASTs, complex expressions, matrices fully generated/parsed
    * All generating/parsing satisfies precedence

### Test Summary:
__________________________________________
    * Associativity, precedence, nested expressions, and function calls all have been tested, individually and/or part of other tests
    * The tests gradually and generally become more complex the further in the test file
    * If a complex test passes, it subsequently means all other tests it involves should pass too

### Verifying Objectives:
___________________________________________
### Parser passes unit tests
    * Parser successfully parses additive, multiplicative, unary, transpose, postfix precedence and associativity
        - Done through test functions in test_parser_expressions.py; PyTest "assert" used to verify parser identifies correectly

### ASTs, complex expressions, matrices fully generated/parsed
    * ASTs generated based off of precedence and associativity and correct
        - Correct nodes generated in correct order/precedence/associativity
        - ASTs should look complete, 
    * Complex expressions successfully parsed
        - All types of expressions, operators, operands identified
        - Precedence and associativity correct
        - Done by using PyTest "assert" to compare parser's results to manually determined results
    * Matrices generated and parsed correctly
        - Manually verify generated matrices
        - Manually verify parser can parse matrices correctly
        - Matrices should look like normal matrices with specified dimensions and elements
        - Parsing matrices should return correct results for interacting with specific elements and matrix functions (tranpose, postfix)

### All ASTs and matrices should be correctly generated and parsed, all expressions correctly parsed
    * Everything follows correct precedence and associativity, even with complex expressions
    * ASTs are fully generated with each node properly associated
    * Matrices can have expressions/arithmetic in their indices
    * Matrix access expressions can be children of binary or other expressions
    * Complex expressions containing all precedence levels and numerous nested expressions are parsed correctly

### General list of more objectives to test (as of writing this section)
__________________________________________
    (NOTE: this is an unverified list. Verify that these things are necessary before taking the time to implement.)
    * DONE - Transpose of matrix literal
    * Function call with multiple arguments
    * DONE - Nested function calls
    * DONE - Arithmetic in row index
    * DONE - Arithmetic in column index
    * DONE - Matrix access inside arithmetic
    * DONE - Binary expression with transpose
    * DONE - Binary expression with unary negation
    * DONE - Function call with arithmetic
    * DONE - Negation, parentheses and transpose
    * DONE - Expression combining all precedence levels