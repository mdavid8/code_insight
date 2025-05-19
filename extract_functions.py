# This script extracts function definitions from a Python source file and writes them to a CSV file.
# It uses the Abstract Syntax Tree (AST) module to parse the source code and identify function definitions.

import ast
import csv
import sys

def extract_functions(source_path, csv_path):
    # Read source code
    with open(source_path, "r", encoding="utf-8") as f:
        source_lines = f.readlines()
        source_code = "".join(source_lines)

    # Parse AST
    tree = ast.parse(source_code)

    # Prepare output CSV
    with open(csv_path, mode="w", newline="", encoding="utf-8") as out_csv:
        writer = csv.writer(out_csv)
        # Optional header row
        writer.writerow(["function_signature", "source_code"])

        # Walk through AST, find function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Function name & argument list
                func_name = node.name
                arg_names = []
                # Positional args
                for arg in node.args.args:
                    arg_names.append(arg.arg)
                # *args
                if node.args.vararg:
                    arg_names.append("*" + node.args.vararg.arg)
                # Keyword-only args
                for arg in node.args.kwonlyargs:
                    arg_names.append(arg.arg + "=?")
                # **kwargs
                if node.args.kwarg:
                    arg_names.append("**" + node.args.kwarg.arg)

                function_signature = f"{func_name}({', '.join(arg_names)})"

                # Extract source code for lines [lineno-1 : end_lineno]
                start = node.lineno - 1
                end = node.end_lineno
                func_src = "".join(source_lines[start:end])
                print(f"{end-start+1} lines in {func_name}")

                # Write to CSV
                writer.writerow([function_signature, func_src])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_functions.py <source_file.py> <output.csv>")
        sys.exit(1)
    extract_functions(sys.argv[1], sys.argv[2])
