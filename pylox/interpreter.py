"""Implements Interpreter"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
from .expr import Expr, Literal, Grouping, Binary, Unary, Ternery, Variable, \
        Assign, Logical, Call
from .stmt import Stmt, Expression, Print, Var, Block, If, While, Break, \
        Function, Return
from .lexer import TokenType, Token
from .callable import LoxCallable, LoxFunction
from .environment import Environment, UNINITIALIZED
from .errors import LoxRuntimeError
from . import errors
from . import builtin

if TYPE_CHECKING:
    from .pylox import ErrorReporter


class GlobalEnvironment(Environment):
    def __init__(self):
        super().__init__()

        self.define(Token(None, "time", None),
                    builtin.LoxTime())


class Interpreter(Expr.Visitor, Stmt.Visitor):
    error_reporter: ErrorReporter
    global_environment: Environment
    environment: Environment
    break_loop: bool

    def __init__(self, error_reporter: ErrorReporter):
        self.error_reporter = error_reporter
        self.global_environment = GlobalEnvironment()
        self.environment = self.global_environment
        self.break_loop = False

    def interpret(self, statements: list[Stmt]):
        try:
            for stmt in statements:
                self.execute(stmt)
        except LoxRuntimeError as error:
            self.error_reporter.report_runtime(error.token.position,
                                               error.message)

    def execute(self, stmt: Stmt):
        stmt.accept(self)

    def execute_block(self,
                      statements: list[Stmt],
                      environment: Environment):
        previous_environment: Environment = self.environment

        try:
            self.environment = environment

            for stmnt in statements:
                if self.break_loop:
                    break
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
        raise LoxRuntimeError(operator, "Operand must be a number.")

    def __check_number_operands(self,
                                operator: Token,
                                left: object,
                                right: object):
        if isinstance(left, float) and isinstance(right, float):
            return
        raise LoxRuntimeError(operator, "Both operands mus be numbers.")

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

    def visit_call_expr(self, expr: Call):
        callee = self.evaluate(expr.callee)
        arguments: list = []
        for arg in expr.arguments:
            arguments.append(self.evaluate(arg))

        if not isinstance(callee, LoxCallable):
            raise LoxRuntimeError(
                    expr.paren,
                    "Can only call functions and classes.")

        function: LoxCallable = callee
        if len(arguments) != function.arity():
            raise LoxRuntimeError(
                    expr.paren,
                    "Expected " + str(function.arity())
                    + " arguments, but got "
                    + str(len(arguments)) + "."
                )

        return function.call(self, arguments)

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
                        return str(left) + right
                    except ValueError:
                        raise LoxRuntimeError(
                                expr.operator,
                                "Cannot convert '"+str(left)+"' to string.")
                if isinstance(left, str) and isinstance(right, float):
                    try:
                        return left + str(right)
                    except ValueError:
                        raise LoxRuntimeError(
                                expr.operator,
                                "Cannot convert '"+str(right)+"' to str.")
                raise LoxRuntimeError(
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
                    raise LoxRuntimeError(expr.operator,
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

    def visit_while_stmt(self, stmt: While):
        while not self.break_loop \
                and self.__is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)
        self.break_loop = False

    def visit_print_stmt(self, stmt: Print):
        print(self.stringify(self.evaluate(stmt.expression)))

    def visit_var_stmt(self, stmt: Var):
        value = UNINITIALIZED
        if stmt.initializer is not None:
            value = self.evaluate(stmt.initializer)
        self.environment.define(stmt.name, value)

    def visit_function_stmt(self, stmt: Function):
        function: LoxFunction = LoxFunction(stmt, self.environment)
        self.environment.define(stmt.name, function)

    def visit_block_stmt(self, stmt: Block):
        self.execute_block(stmt.statements,
                           Environment(self.environment))

    def visit_break_stmt(self, stmt: Break):
        self.break_loop = True

    def visit_return_stmt(self, stmt: Return):
        if stmt.value is None:
            raise errors.LoxReturn(None)
        value = self.evaluate(stmt.value)
        raise errors.LoxReturn(value)
