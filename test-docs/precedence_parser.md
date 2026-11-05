### Test Objectives:
__________________________________________
    * Parser passes unit tests
    * ASTs, complex expressions, matrices fully generated/parsed
    * All generating/parsing satisfies precedence

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

### General list of more objectives to test (as of writing this section)
__________________________________________
    (NOTE: this is an unverified list. Verify that these things are necessary before taking the time to implement.)
    * Transpose of matrix literal
    * Function call with multiple arguments
    * Nested function calls
    * Arithmetic in row index
    * Arithmetic in column index
    * Matrix access inside arithmetic
    * Binary expression with transpose
    * Binary expression with unary negation
    * DONE - Function call with arithmetic
    * Negation, parentheses and transpose
    * Expression combining all precedence levels