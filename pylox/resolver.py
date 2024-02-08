from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Deque, TYPE_CHECKING, Union
from . import stmt
from . import expr
from . import interpreter as intpr
from .lexer import Token

if TYPE_CHECKING:
    from .pylox import ErrorReporter


@dataclass
class VarState:
    token: Token
    defined: bool
    used: bool
    local_index: int


class Resolver(stmt.Stmt.Visitor, expr.Expr.Visitor):
    interpreter: intpr.Interpreter
    scopes: Deque[dict[str, VarState]]
    error_reporter: ErrorReporter

    def __init__(self,
                 interpreter: intpr.Interpreter,
                 error_reporter: ErrorReporter):
        self.interpreter = interpreter
        self.scopes = deque()
        self.error_reporter = error_reporter

    def resolve_stmt(self, statement: stmt.Stmt):
        statement.accept(self)

    def resolve_stmt_list(self, stmts: list[stmt.Stmt]):
        for statement in stmts:
            self.resolve_stmt(statement)

    def resolve_expr(self, expression: expr.Expr):
        expression.accept(self)

    def __begin_scope(self):
        self.scopes.append({})

    def __end_scope(self):
        scope: dict[str, VarState] = self.scopes.pop()
        for name, state in scope.items():
            if not state.used:
                self.error_reporter.report_resolver(
                        state.token.position,
                        "Local variable '" + name
                        + "' defined but never used.")

    def __declare(self, name: Token):
        """Add variable to current scope and mark it as not ready to use"""
        if len(self.scopes) == 0:
            return

        scope = self.scopes[-1]
        if name.lexeme in scope:
            self.error_reporter.report_resolver(
                    name.position,
                    "There is already a variable with name '" + name.lexeme
                    + "' in this scope.")
        idx = len(scope)
        scope[name.lexeme] = VarState(name, False, False, idx)

    def __define(self, name: Token):
        """Mark variable as ready to use"""
        if len(self.scopes) == 0:
            return
        self.scopes[-1][name.lexeme].defined = True

    def __resolve_local(self, var: Union[expr.Expr, stmt.Stmt], name: Token):
        for i, scope in enumerate(reversed(self.scopes)):
            if name.lexeme in scope:
                self.interpreter.resolve(
                        var,
                        i,
                        scope[name.lexeme].local_index)
                scope[name.lexeme].used = True
                return

    def __resolve_function(self, fun: expr.Function):
        self.__begin_scope()
        for param in fun.params:
            self.__declare(param)
            self.__define(param)
        self.resolve_stmt_list(fun.body)
        self.__end_scope()

    def visit_block_stmt(self, block: stmt.Block):
        self.__begin_scope()
        self.resolve_stmt_list(block.statements)
        self.__end_scope()

    def visit_var_stmt(self, var: stmt.Var):
        self.__declare(var.name)

        if var.initializer is not None:
            self.resolve_expr(var.initializer)
        self.__define(var.name)

    def visit_variable_expr(self, var: expr.Variable):
        if len(self.scopes) > 0 \
                and var.name.lexeme in self.scopes[-1] \
                and not self.scopes[-1][var.name.lexeme].defined:
            self.error_reporter.report_resolver(
                    var.name.position,
                    "Can't read local variable in its own initializer.")
        self.__resolve_local(var, var.name)

    def visit_assign_expr(self, assign: expr.Assign):
        self.resolve_expr(assign.value)
        self.__resolve_local(assign, assign.name)

    def visit_fundef_stmt(self, fundef: stmt.FunDef):
        self.__declare(fundef.name)
        self.__define(fundef.name)

        self.resolve_expr(fundef.function)

    def visit_function_expr(self, fun: expr.Function):
        self.__begin_scope()
        for param in fun.params:
            self.__declare(param)
            self.__define(param)
        self.resolve_stmt_list(fun.body)
        self.__end_scope()

    def visit_binary_expr(self, bin_expr: expr.Binary):
        self.resolve_expr(bin_expr.left)
        self.resolve_expr(bin_expr.right)

    def visit_break_stmt(self, break_stmt: stmt.Break):
        pass

    def visit_call_expr(self, call: expr.Call):
        for arg in call.arguments:
            self.resolve_expr(arg)
        self.resolve_expr(call.callee)

    def visit_expression_stmt(self, expr_stmt: stmt.Expression):
        self.resolve_expr(expr_stmt.expression)

    def visit_grouping_expr(self, group: expr.Grouping):
        self.resolve_expr(group.expression)

    def visit_if_stmt(self, if_stmt: stmt.If):
        self.resolve_expr(if_stmt.condition)
        self.resolve_stmt(if_stmt.then_branch)
        if if_stmt.else_branch is not None:
            self.resolve_stmt(if_stmt.else_branch)

    def visit_literal_expr(self, literal: expr.Literal):
        pass

    def visit_logical_expr(self, logical: expr.Logical):
        self.resolve_expr(logical.left)
        self.resolve_expr(logical.right)

    def visit_print_stmt(self, pr: stmt.Print):
        self.resolve_expr(pr.expression)

    def visit_return_stmt(self, ret: stmt.Return):
        if ret.value is not None:
            self.resolve_expr(ret.value)

    def visit_ternery_expr(self, ternery: expr.Ternery):
        self.resolve_expr(ternery.condition)
        self.resolve_expr(ternery.then_expr)
        self.resolve_expr(ternery.else_expr)

    def visit_unary_expr(self, unary: expr.Unary):
        self.resolve_expr(unary.right)

    def visit_while_stmt(self, while_stmt: stmt.While):
        self.resolve_expr(while_stmt.condition)
        self.resolve_stmt(while_stmt.body)

    def visit_class_stmt(self, klass: stmt.Class):
        self.__declare(klass.name)
        self.__define(klass.name)
        self.__resolve_local(klass, klass.name)

    def visit_get_expr(self, get: expr.Get):
        self.resolve_expr(get.object)

    def visit_set_expr(self, s: expr.Set):
        self.resolve_expr(s.value)
        self.resolve_expr(s.object)
