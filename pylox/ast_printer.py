"""
Helper class to print the ast.

Also simple application of the visitor pattern.
"""
from .ast import Visitor, Expr, Binary, Unary, Grouping, Literal

class AstPrinter(Visitor):
    def print(self, expr: Expr):
        print(expr.accept(self))
    
    def __parenthesize(self, name: str, exprs: list[Expr]):
        parts = ["(", name]
        for expr in exprs:
            parts.append(expr.accept(self))
        parts.append(")")
        return " ".join(parts)
    
    def visit_binary_expr(self, expr: Binary):
        return self.__parenthesize(str(expr.operator.lexeme), [expr.left, expr.right])
    
    def visit_unary_expr(self, expr: Unary):
        return self.__parenthesize(str(expr.operator.lexeme), [expr.right])
    
    def visit_grouping_expr(self, expr: Grouping):
        return self.__parenthesize("group", [expr.expression])
    
    def visit_literal_expr(self, expr: Literal):
        return "nil" if expr.value == 0 else str(expr.value)
