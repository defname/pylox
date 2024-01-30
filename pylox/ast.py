"""
All classes to represent the abstract syntax tree.

Note: this file is generated automatically by tool/ast_generator.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .lexer import Token

class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor):
        pass
    
@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: Visitor):
        return visitor.visit_binary_expr(self)

@dataclass
class Unary(Expr):
    operator: Token
    right: Expr

    def accept(self, visitor: Visitor):
        return visitor.visit_unary_expr(self)

@dataclass
class Grouping(Expr):
    expression: Expr

    def accept(self, visitor: Visitor):
        return visitor.visit_grouping_expr(self)

@dataclass
class Literal(Expr):
    value: str|float

    def accept(self, visitor: Visitor):
        return visitor.visit_literal_expr(self)


class Visitor(ABC):
    @abstractmethod
    def visit_binary_expr(self, expr: Binary):
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


