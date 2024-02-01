"""
All classes to represent the abstract syntax tree.

Note: this file is generated automatically by tool/ast_generator.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union
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

        @abstractmethod
        def visit_var_stmt(self, stmt: Var):
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


@dataclass
class Var(Stmt):
    name: Token
    initializer: Union[Expr, None]

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_var_stmt(self)

