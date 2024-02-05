"""
All classes to represent the abstract syntax tree.

Note: this file is generated automatically by tool/ast_generator.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from .lexer import Token, LiteralType
from . import stmt


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor):
        pass

    class Visitor(ABC):
        @abstractmethod
        def visit_binary_expr(self, expr: Binary):
            pass

        @abstractmethod
        def visit_call_expr(self, expr: Call):
            pass

        @abstractmethod
        def visit_unary_expr(self, expr: Unary):
            pass

        @abstractmethod
        def visit_grouping_expr(self, expr: Grouping):
            pass

        @abstractmethod
        def visit_literal_expr(self, expr: Literal):
            pass

        @abstractmethod
        def visit_ternery_expr(self, expr: Ternery):
            pass

        @abstractmethod
        def visit_variable_expr(self, expr: Variable):
            pass

        @abstractmethod
        def visit_assign_expr(self, expr: Assign):
            pass

        @abstractmethod
        def visit_logical_expr(self, expr: Logical):
            pass

        @abstractmethod
        def visit_function_expr(self, expr: Function):
            pass


@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_binary_expr(self)


@dataclass
class Call(Expr):
    callee: Expr
    paren: Token
    arguments: list[Expr]

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_call_expr(self)


@dataclass
class Unary(Expr):
    operator: Token
    right: Expr

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_unary_expr(self)


@dataclass
class Grouping(Expr):
    expression: Expr

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_grouping_expr(self)


@dataclass
class Literal(Expr):
    value: LiteralType

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_literal_expr(self)


@dataclass
class Ternery(Expr):
    condition: Expr
    then_expr: Expr
    else_expr: Expr

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_ternery_expr(self)


@dataclass
class Variable(Expr):
    name: Token

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_variable_expr(self)


@dataclass
class Assign(Expr):
    name: Token
    value: Expr

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_assign_expr(self)


@dataclass
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_logical_expr(self)


@dataclass
class Function(Expr):
    params: list[Token]
    body: list[stmt.Stmt]

    def accept(self, visitor: Expr.Visitor):
        return visitor.visit_function_expr(self)

