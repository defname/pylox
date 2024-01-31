"""
Provides the Parser class.

The grammar is defined by:

    expression  -> equality
    equality    -> comparision ( ("!=" | "==") comparision )*
    comparision -> term ( ( ">" | ">=" | "<" | "<=" ) term )*
    term        -> factor ( ( "-" | "+" ) factor )*
    factor      -> unary ( ( "/"  | "*" ) unary )*
    unary       -> ( "!" | "-" ) unary | primary
    primary     -> NUMBER | STRING
                   | "true" | "false" | "nil"
                   | "(" expression ")"
"""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING
from .lexer import Token, TokenType
from .ast import Expr, Binary, Unary, Grouping, Literal

if TYPE_CHECKING:
    from .pylox import ErrorReporter


class ParseError(Exception):
    """Raised if Parser enters panic mode"""
    pass


class Parser:
    """Class to parse the gramme defined above"""
    tokens: list[Token]
    current: int
    error_reporter: ErrorReporter

    def __init__(self, tokens: list[Token], error_reporter: ErrorReporter):
        self.tokens = tokens
        self.current = 0
        self.error_reporter = error_reporter

    def parse(self) -> Expr|None:
        try:
            return self.__expression()
        except ParseError:
            return None

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
        return self.__equality()

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

        return self.__primary()

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


