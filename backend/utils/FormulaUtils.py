import ast
from typing import Dict, Callable
import pandas as pd

DANGEROUS_KEYWORDS = {
    "import", "eval", "exec", "open", "os", "sys",
    "subprocess", "__import__", "__globals__", "__class__"
}

ALLOWED_BUILT_IN_FUNCTIONS = {
    "str": str,
    "int": int,
    "bool": bool,
    "float": float,
    "round": round,
    "abs": abs,
    "len": len,
    "lower": str.lower,
    "upper": str.upper,
    "set": set,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "sum": sum,
}

class FormulaValidationError(Exception):
    pass

class FormulaSyntaxError(Exception):
    pass

class FormulaNotAllowedError(Exception):
    pass

class FormulaInvalidError(Exception):
    pass

class FormulaNotCallableError(Exception):
    pass


def validate_formula(formula: str):
    """
    Checks formula syntax and prevents dangerous code.
    Raises ValueError if invalid or unsafe.

    Usage:
    try:
        validate_formula(formula_str)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    """
    try:
        tree = ast.parse(formula, mode="exec")
    except SyntaxError as e:
        raise FormulaSyntaxError(f"Syntax error in formula: {e}")

    # Traverse AST and check for dangerous usage
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in DANGEROUS_KEYWORDS:
                raise FormulaNotAllowedError(f"Usage of '{node.id}' is not allowed")
        elif isinstance(node, ast.Attribute):
            attr = getattr(node, 'attr', '')
            if attr.startswith("__"):
                raise FormulaNotAllowedError("Usage of __magic__ attributes is not allowed")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in DANGEROUS_KEYWORDS:
                raise FormulaNotAllowedError(f"Calling '{func.id}' is not allowed")

    # Optionally enforce structure: only lambda or def transform
    func_defs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    lambdas = [n for n in ast.walk(tree) if isinstance(n, ast.Lambda)]

    if not func_defs and not lambdas:
        raise FormulaValidationError("Formula must be a lambda or a function definition")

    if func_defs:
        if func_defs[0].name != "transform":
            raise FormulaValidationError("Function must be named 'transform'")

    return True


def compile_formula_to_func(code: str, allowed_functions: Dict[str, Callable] = None):
    """
    Compiles a user-defined formula (lambda or def) into a callable function.

    Parameters:
    - code: str — formula as string, e.g., "lambda x: x * 0.9"
    - allowed_functions: dict[str, function] — safe, user-defined callable whitelist

    Returns:
    - callable function

    Raises:
    - ValueError if the formula is unsafe or invalid
    """

    # Validate formula safety
    validate_formula(code)

    # Prepare safe globals
    safe_globals = {"__builtins__": {}}
    if allowed_functions:
        for name, func in allowed_functions.items():
            if callable(func):
                safe_globals[name] = func
            else:
                raise FormulaNotCallableError(f"{name} is not a callable")

    try:
        # Evaluate code (only lambda or def allowed by validation)
        func = eval(code, safe_globals, {})
        if not callable(func):
            raise FormulaNotCallableError("The compiled object is not callable")
        return func
    except Exception as e:
        raise FormulaInvalidError(f"Invalid formula: {e}")

def apply_formula_to_column(
    df: pd.DataFrame,
    column_name: str,
    formula: str,
    allowed_functions: dict = None,
) -> pd.Series:
    """
    Applies a user-defined formula to a column of a DataFrame.
    :param df: DataFrame
    :param column_name: Column name
    :param formula: Formula as string, e.g., "lambda x: x * 0.9"
    :param allowed_functions: dict[str, function].
    :return: Series with the result of applying the formula to the column

    Usage:
        df = pd.DataFrame({'x': [1, 2, 3]})
        result = apply_formula_to_column(df, 'x', formula, allowed_functions={'increment': increment, 'square': square})
    """
    if not allowed_functions or not isinstance(allowed_functions, dict):
        allowed_functions = {}

    allowed_functions.update(ALLOWED_BUILT_IN_FUNCTIONS)

    if column_name not in df.columns:
        raise RuntimeError(f"Column '{column_name}' not found in DataFrame")
    try:
        func = compile_formula_to_func(formula, allowed_functions or {})
        return df[column_name].apply(func)
    except Exception as e:
        raise RuntimeError(f"Error applying formula to column '{column_name}': {e}")



def apply_formula_to_row(row: dict, formula: str, allowed_functions: dict):
    """
    Apply a formula (e.g. lambda row: row["a"] + row["b"]) to a row dict.
    """
    if not allowed_functions or not isinstance(allowed_functions, dict):
        allowed_functions = {}

    allowed_functions.update(ALLOWED_BUILT_IN_FUNCTIONS)

    try:
        func = compile_formula_to_func(formula, allowed_functions or {})
        return func(row)
    except Exception as e:
        raise RuntimeError(f"Error applying formula to row (formula: {formula}): {e}")

def increment(x):
    return x + 1

def square(x):
    return x ** 2

def calculate(x):
    return increment(square(x))

def calculate_row(row):
    return row["a"] + row["b"]

if __name__ == "__main__":
    formula = "lambda x: str(calculate(x))"
    func = compile_formula_to_func(formula, {"calculate": calculate, "str": str})
    print(func(2))  # Output: 3


    formula = "lambda row: calculate_row(row)"
    func = compile_formula_to_func(formula, {"calculate_row": calculate_row})
    print(func({"a": 1, "b": 2}))  # Output: 3
