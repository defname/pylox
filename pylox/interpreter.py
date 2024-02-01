"""Implements Interpreter"""
from __future__ import annotations
from .expr import Expr, Literal, Grouping, Binary, Unary, Ternery
from .stmt import Stmt, Expression, Print
from .lexer import TokenType, Token
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .pylox import ErrorReporter


class RuntimeError(Exception):
    def __init__(self,
                 token: Token,
                 message: str,
                 *args: object):
        super().__init__(message, args)
        self.token = token
        self.message = message


class Interpreter(Expr.Visitor, Stmt.Visitor):
    error_reporter: ErrorReporter

    def __init__(self, error_reporter: ErrorReporter):
        self.error_reporter = error_reporter

    def interpret(self, statements: list[Stmt]):
        try:
            for stmt in statements:
                self.execute(stmt)
        except RuntimeError as error:
            self.error_reporter.report_runtime(error.token.position,
                                               error.message)

    def execute(self, stmt: Stmt):
        stmt.accept(self)

    def __check_number_operand(self, operator: Token, operand: object):
        if isinstance(operand, float):
            return
        raise RuntimeError(operator, "Operand must be a number.")

    def __check_number_operands(self,
                                operator: Token,
                                left: object,
                                right: object):
        if isinstance(left, float) and isinstance(right, float):
            return
        raise RuntimeError(operator, "Both operands mus be numbers.")

    def __is_truthy(self, operand: object):
        if operand is None or (isinstance(operand, bool) and not operand):
            return False
        return True

    def __is_equal(self, left: object, right: object):
        return left == right

    def evaluate(self, expr: Expr):
        return expr.accept(self)

    def visit_literal_expr(self, expr: Literal):
        return expr.value

    def visit_grouping_expr(self, expr: Grouping):
        return self.evaluate(expr.expression)

    def visit_unary_expr(self, expr: Unary):
        right: object = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.MINUS:
                self.__check_number_operand(expr.operator, right)
                return -float(right)
            case TokenType.BANG:
                return not self.__is_truthy(right)

        return None

    def visit_binary_expr(self, expr: Binary):
        left: Any = self.evaluate(expr.left)
        right: Any = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.EQUAL_EQUAL:
                return self.__is_equal(left, right)
            case TokenType.BANG_EQUAL:
                return not self.__is_equal(left, right)
            case TokenType.GREATER:
                self.__check_number_operands(expr.operator, left, right)
                return left > right
            case TokenType.GREATER_EQUAL:
                self.__check_number_operands(expr.operator, left, right)
                return left >= right
            case TokenType.LESS:
                self.__check_number_operands(expr.operator, left, right)
                return left < right
            case TokenType.LESS_EQUAL:
                self.__check_number_operands(expr.operator, left, right)
                return left <= right
            case TokenType.PLUS:
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                if isinstance(left, float) and isinstance(right, float):
                    return left + right
                # implicit str conversion
                if isinstance(left, float) and isinstance(right, str):
                    try:
                        return left + float(right)
                    except ValueError:
                        raise RuntimeError(
                                expr.operator,
                                "Cannot convert '"+right+"' to number.")
                if isinstance(left, str) and isinstance(right, float):
                    try:
                        return float(left) + right
                    except ValueError:
                        raise RuntimeError(
                                expr.operator,
                                "Cannot convert '"+left+"' to number.")
                raise RuntimeError(
                        expr.operator,
                        "Both operands have to be strings or numbers"
                    )
            case TokenType.MINUS:
                self.__check_number_operands(expr.operator, left, right)
                return float(left) - float(right)
            case TokenType.STAR:
                self.__check_number_operands(expr.operator, left, right)
                return float(left) * float(right)
            case TokenType.SLASH:
                self.__check_number_operands(expr.operator, left, right)
                if right == 0:
                    raise RuntimeError(expr.operator,
                                       "Do not divide by zero!")
                return float(left) / float(right)

    def visit_ternery_expr(self, expr: Ternery):
        condition = self.evaluate(expr.condition)
        if self.__is_truthy(condition):
            return self.evaluate(expr.then_expr)
        return self.evaluate(expr.else_expr)

    def visit_expression_stmt(self, stmt: Expression):
        self.evaluate(stmt.expression)

    def visit_print_stmt(self, stmt: Print):
        print(self.evaluate(stmt.expression))
