"""
Helper class to print the ast.

Also simple application of the visitor pattern.
"""
from .expr import Expr, Binary, Unary, Grouping, Literal, Ternery, Call

class AstPrinter(Expr.Visitor):
    def print(self, expr: Expr):
        print(expr.accept(self))

    def __parenthesize(self, name: str, exprs: list[Expr]):
        parts = ["(", name]
        for expr in exprs:
            parts.append(expr.accept(self))
        parts.append(")")
        return " ".join(parts)

    def visit_binary_expr(self, expr: Binary):
        return self.__parenthesize(
                str(expr.operator.lexeme),
                [expr.left, expr.right])

    def visit_unary_expr(self, expr: Unary):
        return self.__parenthesize(str(expr.operator.lexeme), [expr.right])

    def visit_grouping_expr(self, expr: Grouping):
        return self.__parenthesize("group", [expr.expression])

    def visit_literal_expr(self, expr: Literal):
        return "nil" if expr.value is None else str(expr.value)

    def visit_ternery_expr(self, expr: Ternery):
        return self.__parenthesize("?:",
                                   [
                                       expr.condition,
                                       expr.then_expr,
                                       expr.else_expr
                                    ])

    def visit_call_expr(self, expr: Call):
        return "FUNCTION CALL"
