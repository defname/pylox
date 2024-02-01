"""
All classes to represent the abstract syntax tree.

Note: this file is generated automatically by tool/ast_generator.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .lexer import Token, LiteralType
from .expr import Expr


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor):
        pass

    class Visitor(ABC):
        @abstractmethod
        def visit_expression_stmt(self, stmt: Expression):
            pass

        @abstractmethod
        def visit_print_stmt(self, stmt: Print):
            pass


@dataclass
class Expression(Stmt):
    expression: Expr

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_expression_stmt(self)


@dataclass
class Print(Stmt):
    expression: Expr

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_print_stmt(self)

