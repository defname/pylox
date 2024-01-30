from pylox.lexer import TokenType, Token, SourcePosition
from pylox.ast import Visitor, Expr, Binary, Unary, Grouping, Literal
from pylox.ast_printer import AstPrinter

class RPN(Visitor):
    def print(self, expr: Expr):
        print(expr.accept(self))
    
    def visit_binary_expr(self, expr: Binary):
        return expr.left.accept(self) + " " + expr.right.accept(self) + " " + expr.operator.lexeme
    
    def visit_unary_expr(self, expr: Unary):
        return expr.right.accept(self) + " " + expr.operator.lexeme
    
    def visit_grouping_expr(self, expr: Grouping):
        return expr.expression.accept(self) + " group"
    
    def visit_literal_expr(self, expr: Literal):
        return "nil" if expr.value == 0 else str(expr.value)


if __name__ == "__main__":

    expr = Binary(
        Unary(Token(TokenType.MINUS, "-", None), Literal(123)),
        Token(TokenType.STAR, "*", None),
        Grouping(Literal(123.123))
    )
    RPN().print(expr)