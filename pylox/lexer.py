"""
Module containing the Lexer class and everything it needs (except of
the ErrorReporter).
"""
from __future__ import annotations
from enum import Enum
import dataclasses
import copy

from typing import TYPE_CHECKING
from typing import Union

if TYPE_CHECKING:
    from typing import Final
    from .pylox import ErrorReporter

TokenType = Enum("TokenType", [
    # single-character tokens
    "LEFT_PAREN", "RIGHT_PAREN", "LEFT_BRACE", "RIGHT_BRACE",
    "COMMA", "DOT", "MINUS", "PLUS", "SEMICOLON", "SLASH", "STAR",
    "QUESTIONMARK", "COLON",

    # one or two character tokens
    "BANG", "BANG_EQUAL",
    "EQUAL", "EQUAL_EQUAL",
    "GREATER", "GREATER_EQUAL",
    "LESS", "LESS_EQUAL",

    # literals
    "IDENTIFIER", "STRING", "NUMBER",

    # keywords
    "AND", "CLASS", "ELSE", "FALSE", "FUN", "FOR", "IF", "NIL", "OR",
    "PRINT", "RETURN", "SUPER", "THIS", "TRUE", "VAR", "WHILE", "BREAK",

    # end-of-file
    "EOF"
])

KEYWORD_TYPE: Final[dict[str, TokenType]] = {
    "and": TokenType.AND,
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "fun": TokenType.FUN,
    "for": TokenType.FOR,
    "if": TokenType.IF,
    "nil": TokenType.NIL,
    "or": TokenType.OR,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
    "super": TokenType.SUPER,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "var": TokenType.VAR,
    "while": TokenType.WHILE,
    "break": TokenType.BREAK
}


@dataclasses.dataclass
class SourcePosition:
    """
    Represents a position in the source code
    """
    line: int = 0
    """Current line (could also be calculated, but the information will be available, so...)"""
    start: int = 0
    """Start of the current (maybe) token"""
    current: int = 0
    """Current position of the cursor"""

    def __str__(self):
        return f"line: {self.line}, start: {self.start}, position: {self.current}"


LiteralType = Union[str, float, bool, None]


@dataclasses.dataclass
class Token:
    """
    Represents a token.
    
    Including additional information, like line number, position and lexeme
    """
    type: TokenType
    lexeme: str
    position: SourcePosition
    literal: LiteralType = None

    def __str__(self):
        return str(self.type) + " " + str(self.lexeme) + " " + str(self.literal)


class Lexer:
    """
    The Lexer with the scan method, which creates a list of tokens from the source code
    """
    def __init__(self, source: str, error_reporter: ErrorReporter):
        self.source: str = source
        self.tokens: list[Token] = list()
        self.error_reporter = error_reporter
        self.had_error = False

        self.position = SourcePosition(1, 0, 0)

    def scan(self) -> list[Token]:
        """
        Scan the source and split it up into usable Tokens.
        """
        while not self.__is_at_end():
            self.position.start = self.position.current
            self.__scan_token()

        self.__add_token(TokenType.EOF)

        return self.tokens
    
    def __scan_token(self):
        c = self.__advance()
        match c:
            # single character tokens
            case "(":
                self.__add_token(TokenType.LEFT_PAREN)
            case ")":
                self.__add_token(TokenType.RIGHT_PAREN)
            case "{":
                self.__add_token(TokenType.LEFT_BRACE)
            case "}":
                self.__add_token(TokenType.RIGHT_BRACE)
            case ",":
                self.__add_token(TokenType.COMMA)
            case ".":
                self.__add_token(TokenType.DOT)
            case ";":
                self.__add_token(TokenType.SEMICOLON)
            case "+":
                self.__add_token(TokenType.PLUS)
            case "-":
                self.__add_token(TokenType.MINUS)
            case "*":
                self.__add_token(TokenType.STAR)
            case "?":
                self.__add_token(TokenType.QUESTIONMARK)
            case ":":
                self.__add_token(TokenType.COLON)

            # whitespaces
            case " ":
                pass
            case "\r":
                pass
            case "\t":
                pass
            # newline
            case "\n":
                self.position.line += 1

            # one or two character tokens
            case "!":
                if self.__match("="):
                    self.__add_token(TokenType.BANG_EQUAL)
                else:
                    self.__add_token(TokenType.BANG)
            case "=":
                if self.__match("="):
                    self.__add_token(TokenType.EQUAL_EQUAL)
                else:
                    self.__add_token(TokenType.EQUAL)
            case "<":
                if self.__match("="):
                    self.__add_token(TokenType.LESS_EQUAL)
                else:
                    self.__add_token(TokenType.LESS)
            case ">":
                if self.__match("="):
                    self.__add_token(TokenType.GREATER_EQUAL)
                else:
                    self.__add_token(TokenType.GREATER)
            
            # "/" and comments
            case "/":
                if not self.__match("/"):
                    self.__add_token(TokenType.SLASH)
                else:
                    while self.__peek() != '\n' and not self.__is_at_end():
                        self.__advance()  # comments are just blasted to nowhere
            
            # string literals
            case "\"":
                while self.__peek() != "\"":
                    if self.__is_at_end():
                        self.error_reporter.report_lex(copy.copy(self.position), "Unfinished string at end of file.")
                        break
                    self.__advance()
                if not self.__is_at_end():
                    self.__advance()  # read ending "
                literal = self.source[self.position.start+1:self.position.current-1]
                self.__add_token(TokenType.STRING, literal)

            case _:
                # numbers
                if Lexer.is_numeric(c):
                    while Lexer.is_numeric(self.__peek()):
                        self.__advance()
                    if self.__peek() == "." and Lexer.is_numeric(self.__peek_next()):
                        self.__advance()
                        while Lexer.is_numeric(self.__peek()):
                            self.__advance()
                    value: float = float(self.source[self.position.start:self.position.current])
                    self.__add_token(TokenType.NUMBER, value)
                # identifier and keywords
                elif Lexer.is_alpha(c):
                    while Lexer.is_alphanumeric(self.__peek()):
                        self.__advance()
                    value: str = self.source[self.position.start:self.position.current]
                    # keywords
                    if value in KEYWORD_TYPE:
                        self.__add_token(KEYWORD_TYPE[value])
                    # identifier
                    else:        
                        self.__add_token(TokenType.IDENTIFIER, value)
                else:
                    self.error_reporter.report_lex(copy.copy(self.position), "Unexpected character.")
                    self.had_error = True
    
    @staticmethod
    def is_numeric(c: str) -> bool:
        """Check if c is a numeric."""
        return '0' <= c <= '9'

    @staticmethod
    def is_alpha(c: str) -> bool:
        """Check if c is a character or an underscore."""
        return 'a' <= c <= 'z' or 'A' <= c <= 'Z' or c == '_'
    
    @staticmethod
    def is_alphanumeric(c: str) -> bool:
        """Check if c is alphanumeric"""
        return Lexer.is_alpha(c) or Lexer.is_numeric(c)

    def __add_token(self, typ: TokenType, literal: LiteralType = None):
        """Add token to the token list."""
        lexeme = self.source[self.position.start:self.position.current]
        self.tokens.append(Token(typ, lexeme, copy.copy(self.position), literal))

    def __is_at_end(self) -> bool:
        return self.position.current >= len(self.source)

    def __advance(self) -> str:
        self.position.current += 1
        return self.source[self.position.current-1]
    
    def __match(self, expect: str) -> bool:
        if self.__is_at_end():
            return False
        if self.source[self.position.current] != expect:
            return False
        
        self.position.current += 1
        return True
    
    def __peek(self) -> str:
        if self.__is_at_end():
            return '\0'
        return self.source[self.position.current]
    
    def __peek_next(self) -> str:
        if self.position.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.position.current+1]
