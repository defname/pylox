"""
All classes to represent the abstract syntax tree.

Note: this file is generated automatically by tool/ast_generator.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
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
        def visit_if_stmt(self, stmt: If):
            pass

        @abstractmethod
        def visit_print_stmt(self, stmt: Print):
            pass

        @abstractmethod
        def visit_var_stmt(self, stmt: Var):
            pass

        @abstractmethod
        def visit_block_stmt(self, stmt: Block):
            pass


@dataclass
class Expression(Stmt):
    expression: Expr

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_expression_stmt(self)


@dataclass
class If(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_if_stmt(self)


@dataclass
class Print(Stmt):
    expression: Expr

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_print_stmt(self)


@dataclass
class Var(Stmt):
    name: Token
    initializer: Optional[Expr]

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_var_stmt(self)


@dataclass
class Block(Stmt):
    statements: list[Stmt]

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_block_stmt(self)

