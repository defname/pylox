"""
All classes to represent the abstract syntax tree.

Note: this file is generated automatically by tool/ast_generator.py
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from .lexer import Token, LiteralType
from . import expr


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
        def visit_while_stmt(self, stmt: While):
            pass

        @abstractmethod
        def visit_fundef_stmt(self, stmt: FunDef):
            pass

        @abstractmethod
        def visit_var_stmt(self, stmt: Var):
            pass

        @abstractmethod
        def visit_block_stmt(self, stmt: Block):
            pass

        @abstractmethod
        def visit_break_stmt(self, stmt: Break):
            pass

        @abstractmethod
        def visit_return_stmt(self, stmt: Return):
            pass

        @abstractmethod
        def visit_class_stmt(self, stmt: Class):
            pass


@dataclass
class Expression(Stmt):
    expression: expr.Expr

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_expression_stmt(self)


@dataclass
class If(Stmt):
    condition: expr.Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_if_stmt(self)


@dataclass
class Print(Stmt):
    expression: expr.Expr

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_print_stmt(self)


@dataclass
class While(Stmt):
    condition: expr.Expr
    body: Stmt

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_while_stmt(self)


@dataclass
class FunDef(Stmt):
    name: Token
    function: expr.Function

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_fundef_stmt(self)


@dataclass
class Var(Stmt):
    name: Token
    initializer: Optional[expr.Expr]

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_var_stmt(self)


@dataclass
class Block(Stmt):
    statements: list[Stmt]

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_block_stmt(self)


@dataclass
class Break(Stmt):
    keyword: Token

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_break_stmt(self)


@dataclass
class Return(Stmt):
    keyword: Token
    value: Optional[expr.Expr]

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_return_stmt(self)


@dataclass
class Class(Stmt):
    name: Token
    methods: list[FunDef]

    def accept(self, visitor: Stmt.Visitor):
        return visitor.visit_class_stmt(self)

