#!/usr/bin/env python3
"""Simple Flask API exposing a stub equation solver."""

from __future__ import annotations

import os
from flask import Flask, jsonify, request
from sympy import symbols, sympify, solve as sympy_solve, S
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from sympy.core.sympify import SympifyError


def parse_equation(equation_str: str):
    equation_str = equation_str.replace("^", "**")

    transformations = standard_transformations + \
        (implicit_multiplication_application,)

    if "=" in equation_str:
        left, right = equation_str.split("=", 1)
        left_expr = parse_expr(left.strip(), transformations=transformations)
        right_expr = parse_expr(right.strip(), transformations=transformations)
        return left_expr - right_expr
    else:
        return parse_expr(equation_str, transformations=transformations)


def solve_equation(equation_str: str, variable: str = "x"):
    equation = parse_equation(equation_str)
    x = symbols(variable)

    if x not in equation.free_symbols:
        result = equation.simplify()
        return ["EVAL", result]

    solutions = sympy_solve(equation, x)

    if not solutions:
        simplified = equation.simplify()
        if simplified == 0:
            return [S.Reals]
    return solutions


def format_solutions(solutions):
    if not solutions:
        return "No solution exists"

    if len(solutions) == 2 and solutions[0] == "EVAL":
        result = solutions[1]
        try:
            if float(result) == int(float(result)):
                return str(int(float(result)))
        except (ValueError, TypeError):
            pass
        result_str = str(result).replace("I", "i")
        return result_str

    if S.Reals in solutions or solutions == S.Reals:
        return "x can be any real number"

    formatted = []
    for sol in solutions:
        sol_str = str(sol).replace("I", "i")
        formatted.append(f"x = {sol_str}")

    if len(formatted) == 1:
        return formatted[0]
    else:
        return " or ".join(formatted)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.get("/solve")
    def solve():
        equation = (request.args.get("equation") or "").strip()

        if not equation:
            return jsonify({"error": "Missing 'equation' query parameter"}), 400

        if len(equation) > 500:
            return jsonify({"error": "Equation too long (max 500 characters)"}), 400

        try:
            solutions = solve_equation(equation, variable="x")
            result_text = format_solutions(solutions)
            return jsonify({"result": result_text}), 200

        except (SympifyError, ValueError, TypeError) as e:
            return jsonify({"error": "Invalid equation syntax. Please check your input."}), 400

        except Exception as e:
            return jsonify({"error": "Failed to solve equation. Please try a simpler form."}), 500

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({"message": "Equation API. Try /solve?equation=1+1"})

    return app


def run() -> None:
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    run()
