"""Implements Interpreter"""
from __future__ import annotations
from .expr import Expr, Literal, Grouping, Binary, Unary, Ternery, Variable, \
        Assign, Logical
from .stmt import Stmt, Expression, Print, Var, Block, If
from .lexer import TokenType, Token
from typing import TYPE_CHECKING, Any, Optional

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


UNINITIALIZED = object()


class Environment:
    """An environment holding variables and their values"""
    values: dict[str, Any]
    enclosing: Optional[Environment]

    def __init__(self, enclosing: Optional[Environment] = None):
        self.values = {}
        self.enclosing = enclosing

    def define(self, name: Token, value: Any = UNINITIALIZED):
        """Define a new variable and initialize it with 'value'"""
        self.values[name.lexeme] = value

    def get(self, name: Token):
        """
        Return the value of the variable with 'name' if it is defined.
        Raise RuntimeError otherwise.
        """
        if name.lexeme in self.values:
            if self.values[name.lexeme] is UNINITIALIZED:
                raise RuntimeError(
                        name,
                        "Uninitialized variable '" + name.lexeme + "'.")
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise RuntimeError(name, "Undefined variable '" + name.lexeme + "'.")

    def assign(self, name: Token, value: Any):
        """
        Assign a value to a variable.
        Raise RuntimeError if the variable doesn't exist.
        """
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise RuntimeError(name,
                           "Undefined variable '" + name.lexeme + "'.")


class Interpreter(Expr.Visitor, Stmt.Visitor):
    error_reporter: ErrorReporter
    environment: Environment

    def __init__(self, error_reporter: ErrorReporter):
        self.error_reporter = error_reporter
        self.environment = Environment()

    def interpret(self, statements: list[Stmt]):
        try:
            for stmt in statements:
                self.execute(stmt)
        except RuntimeError as error:
            self.error_reporter.report_runtime(error.token.position,
                                               error.message)

    def execute(self, stmt: Stmt):
        stmt.accept(self)

    def __execute_block(self,
                        statements: list[Stmt],
                        environment: Environment):
        previous_environment: Environment = self.environment

        try:
            self.environment = environment

            for stmnt in statements:
                self.execute(stmnt)
        finally:
            self.environment = previous_environment

    def stringify(self, value: Any):
        if value is None:
            return "nil"
        return str(value)

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

    ###########################################################################
    # Expr.Visitor
    def visit_literal_expr(self, expr: Literal):
        return expr.value

    def visit_grouping_expr(self, expr: Grouping):
        return self.evaluate(expr.expression)

    def visit_unary_expr(self, expr: Unary):
        right: Any = self.evaluate(expr.right)

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

    def visit_variable_expr(self, expr: Variable):
        return self.environment.get(expr.name)

    def visit_assign_expr(self, expr: Assign):
        value = self.evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    def visit_logical_expr(self, expr: Logical):
        left = self.evaluate(expr.left)
        if expr.operator.type == TokenType.OR:
            if self.__is_truthy(left):
                return left
        else:
            if not self.__is_truthy(left):
                return left
        return self.evaluate(expr.right)

    ###########################################################################
    # Stmt.Visitor
    def visit_expression_stmt(self, stmt: Expression):
        self.evaluate(stmt.expression)

    def visit_if_stmt(self, stmt: If):
        condition = self.evaluate(stmt.condition)
        if self.__is_truthy(condition):
            self.execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self.execute(stmt.else_branch)

    def visit_print_stmt(self, stmt: Print):
        print(self.stringify(self.evaluate(stmt.expression)))

    def visit_var_stmt(self, stmt: Var):
        value = UNINITIALIZED
        if stmt.initializer is not None:
            value = self.evaluate(stmt.initializer)
        self.environment.define(stmt.name, value)

    def visit_block_stmt(self, stmt: Block):
        self.__execute_block(stmt.statements,
                            Environment(self.environment))
