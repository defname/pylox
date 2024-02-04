"""
Provides the Parser class.

The grammar is defined by:

    program     -> declaration* EOF

    declaration -> varDecl
                   | statement

    varDecl     -> "var" IDENTIFIER ("=" expression)? ";"

    statement   -> exprStmt
                   | forStmt
                   | ifStmt
                   | printStmt
                   | whileStmt
                   | block
                   | breakStmt

    exprStmt    -> expression ";"
    forStmt     -> "for" "(" (varDecl | exprStmt | ";")
                   expression? ";" expression? ")" statement
    ifStmt      -> "if" "(" expression ")" statement
                   ("else" statement)?
    printStmt   -> "print" expression ";"
    whileStmt   -> "while" "(" expression ")" statement
    block       -> "{" declaration* "}"
    breakStmt   -> "break" ";"

    expression  -> assignment
    assignment  -> IDENTIFIER "=" assignment
                   | logical_or
    logical_or  -> logical_and ("or" logical_and)*
    logical_and -> ternery ("and" ternery)*
    ternery     -> equality ("?" equality ":" ternery)?
    equality    -> comparision ( ("!=" | "==") comparision )*
    comparision -> term ( ( ">" | ">=" | "<" | "<=" ) term )*
    term        -> factor ( ( "-" | "+" ) factor )*
    factor      -> unary ( ( "/"  | "*" ) unary )*
    unary       -> ( "!" | "-" ) unary | call
    call        -> primary ( "(" arguments ")" )*
    arguments   -> expression ( "," expression )*

    primary     -> NUMBER | STRING
                   | "true" | "false" | "nil"
                   | "(" expression ")"
                   | IDENTIFIER
"""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Optional
from .lexer import Token, TokenType
from .expr import Expr, Binary, Unary, Grouping, Literal, Ternery, Variable, \
        Assign, Logical, Call
from .stmt import Stmt, Expression, Print, Var, Block, If, While, Break

if TYPE_CHECKING:
    from .pylox import ErrorReporter

BINARY_OPERATOR_TYPES = [
        TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL, TokenType.GREATER,
        TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL,
        TokenType.MINUS, TokenType.PLUS, TokenType.SLASH, TokenType.STAR
    ]


class ParseError(Exception):
    """Raised if Parser enters panic mode"""
    pass


class Parser:
    """Class to parse the gramma defined above"""
    tokens: list[Token]
    current: int
    error_reporter: ErrorReporter
    nested_loops: int

    def __init__(self, tokens: list[Token], error_reporter: ErrorReporter):
        self.tokens = tokens
        self.current = 0
        self.error_reporter = error_reporter
        self.nested_loops = 0

    def parse(self) -> list[Stmt]:
        """
        Parse tokens and return a list of statements.
        If parser enters panic mode and has to synchronize discard
        this statement.
        """
        statements: list[Stmt] = []
        self.nested_loops = 0

        while not self.__is_at_end():
            stmt = self.__declaration()
            if stmt is not None:
                statements.append(stmt)
        return statements

    def __peek(self) -> Token:
        """Return current token"""
        return self.tokens[self.current]

    def __previous(self) -> Token:
        """Return previous token"""
        return self.tokens[self.current - 1]

    def __is_at_end(self) -> bool:
        """Return True if current token is EOF"""
        return self.__peek().type == TokenType.EOF

    def __advance(self) -> Token:
        """Return current token and increment current"""
        if not self.__is_at_end():
            self.current += 1
        return self.__previous()

    def __check(self, typ: TokenType):
        """Check if current token has type 'typ'"""
        if self.__is_at_end():
            return False
        return self.__peek().type == typ

    def __match(self, types: list[TokenType]):
        """Check if current tokens type if one of types"""
        for typ in types:
            if self.__check(typ):
                self.__advance()
                return True
        return False

    ###########################################################################
    # Statement productions
    def __declaration(self) -> Optional[Stmt]:
        try:
            if self.__match([TokenType.VAR]):
                return self.__var_decl()
            return self.__statement()
        except ParseError:
            self.__synchronize()
            return None

    def __var_decl(self) -> Stmt:
        var_name = self.__consume(TokenType.IDENTIFIER,
                                  "Expect variable name")
        initializer: Optional[Expr] = None
        if self.__match([TokenType.EQUAL]):
            initializer = self.__expression()

        self.__consume(TokenType.SEMICOLON,
                       "Expect ';' after variable declaration.")
        return Var(var_name, initializer)

    def __statement(self) -> Stmt:
        if self.__match([TokenType.IF]):
            return self.__if_statement()

        if self.__match([TokenType.WHILE]):
            return self.__while_statement()

        if self.__match([TokenType.FOR]):
            return self.__for_statement()

        if self.__match([TokenType.PRINT]):
            return self.__print_statement()

        if self.__match([TokenType.LEFT_BRACE]):
            return Block(self.__block())

        if self.__match([TokenType.BREAK]):
            stmt: Optional[Stmt] = self.__break_statement()
            if stmt is not None:
                return stmt
            # otherwise just continue

        return self.__expression_statement()

    def __if_statement(self) -> Stmt:
        self.__consume(TokenType.LEFT_PAREN,
                       "Expect '(' after 'if'.")
        condition: Expr = self.__expression()
        self.__consume(TokenType.RIGHT_PAREN,
                       "Expect ')' after 'if' condition.")

        then_branch: Stmt = self.__statement()
        else_branch: Optional[Stmt] = None

        if self.__match([TokenType.ELSE]):
            else_branch = self.__statement()

        return If(condition, then_branch, else_branch)

    def __while_statement(self) -> Stmt:
        self.__consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition: Expr = self.__expression()
        self.__consume(TokenType.RIGHT_PAREN, "Expect ')' after 'while'.")
        self.nested_loops += 1
        body: Stmt = self.__statement()
        self.nested_loops -= 1

        return While(condition, body)

    def __for_statement(self) -> Stmt:
        self.__consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")
        initializer: Optional[Stmt] = None
        if self.__match([TokenType.SEMICOLON]):
            initializer = None
        elif self.__match([TokenType.VAR]):
            initializer = self.__var_decl()
        else:
            initializer = self.__expression_statement()

        condition: Optional[Expr] = None
        if not self.__check(TokenType.SEMICOLON):
            condition = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment: Optional[Expr] = None
        if not self.__check(TokenType.RIGHT_PAREN):
            increment = self.__expression()
        self.__consume(TokenType.RIGHT_PAREN,
                       "Expect ')' after for clause.")

        self.nested_loops += 1
        body: Stmt = self.__statement()
        self.nested_loops -= 1

        # Build while loop
        if increment is not None:
            body = Block([body, Expression(increment)])

        if condition is None:
            condition = Literal(True)

        body = While(condition, body)

        if initializer is not None:
            body = Block([initializer, body])

        return body

    def __print_statement(self) -> Stmt:
        value: Expr = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Print(value)

    def __expression_statement(self) -> Stmt:
        value: Expr = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(value)

    def __block(self) -> list[Stmt]:
        statements: list[Stmt] = []
        while not self.__check(TokenType.RIGHT_BRACE) \
                and not self.__is_at_end():
            stmt = self.__declaration()
            if stmt is not None:
                statements.append(stmt)

        self.__consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def __break_statement(self) -> Stmt:
        if self.nested_loops == 0:
            raise self.__error(self.__previous(),
                               "'break' is only allowed inside loops")
        self.__consume(TokenType.SEMICOLON,
                       "Expect ';' after 'break'.")
        return Break()

    ###########################################################################
    # Expression productions
    def __binary_expression(
            self,
            operand: Callable[[], Expr],
            operator_types: list[TokenType]) -> Expr:
        """Generic helper method, for all binary expression productions"""
        expr: Expr = operand()

        while self.__match(operator_types):
            operator: Token = self.__previous()
            right: Expr = operand()

            expr = Binary(expr, operator, right)

        return expr

    def __expression(self) -> Expr:
        return self.__assignment()

    def __assignment(self) -> Expr:
        expr: Expr = self.__or()

        if self.__match([TokenType.EQUAL]):
            equals: Token = self.__previous()
            value: Expr = self.__assignment()
            if isinstance(expr, Variable):
                var: Variable = expr
                return Assign(var.name, value)

            self.__error(equals, "Invalid assignment target.")
        return expr

    def __or(self) -> Expr:
        left: Expr = self.__and()

        while self.__match([TokenType.OR]):
            operator: Token = self.__previous()
            right: Expr = self.__and()

            left = Logical(left, operator, right)

        return left

    def __and(self) -> Expr:
        left: Expr = self.__ternery()

        while self.__match([TokenType.AND]):
            operator: Token = self.__previous()
            right: Expr = self.__ternery()

            left = Logical(left, operator, right)

        return left

    def __ternery(self) -> Expr:
        expr: Expr = self.__equality()

        if self.__match([TokenType.QUESTIONMARK]):
            then_expr: Expr = self.__ternery()

            if self.__match([TokenType.COLON]):
                else_expr: Expr = self.__ternery()

            else:
                self.__advance()
                self.error_reporter.report_parser(self.__peek().position,
                                                  "Expect ':'.")
                return self.__ternery()

            expr = Ternery(expr, then_expr, else_expr)

        return expr

    def __equality(self) -> Expr:
        return self.__binary_expression(
                self.__comparision,
                [TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL])

    def __comparision(self) -> Expr:
        return self.__binary_expression(
                self.__term,
                [
                    TokenType.LESS,
                    TokenType.LESS_EQUAL,
                    TokenType.GREATER,
                    TokenType.GREATER_EQUAL
                ])

    def __term(self) -> Expr:
        return self.__binary_expression(
                self.__factor,
                [TokenType.PLUS, TokenType.MINUS])

    def __factor(self) -> Expr:
        return self.__binary_expression(
                self.__unary,
                [TokenType.STAR, TokenType.SLASH])

    def __unary(self) -> Expr:

        if self.__match([TokenType.BANG, TokenType.MINUS]):
            operator: Token = self.__previous()
            right: Expr = self.__unary()
            return Unary(operator, right)

        return self.__call()

    def __call(self) -> Expr:
        expr: Expr = self.__primary()

        while True:
            if self.__match([TokenType.LEFT_PAREN]):
                expr = self.__finish_call(expr)
            else:
                break
        return expr

    def __finish_call(self, callee: Expr) -> Expr:
        arguments: list[Expr] = []
        paren: Optional[Token] = None

        if not self.__check(TokenType.RIGHT_PAREN):
            arguments.append(self.__expression())

            while self.__match([TokenType.COMMA]):
                arguments.append(self.__expression())
        paren = self.__consume(TokenType.RIGHT_PAREN,
                               "Expect ')' after arguments.")

        if len(arguments) >= 255:
            self.error_reporter.report_parser(
                    paren.position,
                    "Can't have more than 255 arguments."
                )

        return Call(callee, paren, arguments)

    def __primary(self) -> Expr:
        if self.__match([TokenType.FALSE]):
            return Literal(False)
        if self.__match([TokenType.TRUE]):
            return Literal(True)

        if self.__match([TokenType.NIL]):
            return Literal(None)

        if self.__match([TokenType.NUMBER, TokenType.STRING]):
            return Literal(self.__previous().literal)

        if self.__match([TokenType.LEFT_PAREN]):
            expr: Expr = self.__expression()
            self.__consume(TokenType.RIGHT_PAREN,
                           "Expect ')' after expression.")
            return Grouping(expr)

        if self.__match([TokenType.IDENTIFIER]):
            return Variable(self.__previous())

        # check for a faulty positioned binary operator
        if self.__match(BINARY_OPERATOR_TYPES):
            self.error_reporter.report_parser(self.__previous().position,
                                              "Left hand operand expected.")
            return self.__primary()

        raise self.__error(self.__peek(), "Expect expression.")

    def __error(self, token: Token, message: str) -> ParseError:
        """Report error with 'message' and return ParseError object"""
        self.error_reporter.report_parser(token.position, message)
        return ParseError()

    def __consume(self, typ: TokenType, message: str) -> Token:
        """
        If current token is of type 'typ' return it and increment current
        :param typ: token type to check for
        :param message: message for ErrorReporter is check fails
        :return: current token (if it has the type 'typ')
        :raiseis: ParseError if type check fails
        """
        if self.__check(typ):
            return self.__advance()

        raise self.__error(self.__peek(), message)

    def __synchronize(self):
        """Skip everything until next expression to resynchronize parser"""
        self.__advance()

        while not self.__is_at_end():
            if self.__previous().type == TokenType.SEMICOLON:
                return

            match self.__peek():
                case TokenType.CLASS:
                    return
                case TokenType.FUN:
                    return
                case TokenType.VAR:
                    return
                case TokenType.FOR:
                    return
                case TokenType.IF:
                    return
                case TokenType.WHILE:
                    return
                case TokenType.PRINT:
                    return
                case TokenType.RETURN:
                    return
            self.__advance()
