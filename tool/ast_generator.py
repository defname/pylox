"""
Provides the function generate_ast to generate a python source code
file containing auto generated classes for the abstract syntax tree.
"""
import sys
from typing import Optional

def generate_ast(base_class_name: str,
                 object_definitions: list[str],
                 output_dir: str,
                 imports: list[str] = []) -> str:
    """
    Generate python sourcecode with class definitions implementing the
    given object_definitions.

    :param object_definitions: list of string of the form
        "class_name : type1 param1, type2 param2, ..."
    :return: generated python source code
    :example: generate_ast("Expr", ["Binary: Expr left, Token operator, Expr right", "Unary: Token operator, Expr right"])
    """
    source: str = \
"""\"\"\"
All classes to represent the abstract syntax tree.

Note: this file is generated automatically by tool/ast_generator.py
\"\"\"

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from .lexer import Token, LiteralType
"""
    for imp in imports:
        source += imp + "\n"
    source += """

class """+base_class_name+"""(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor):
        pass

"""

    source += "    class Visitor(ABC):\n"
    for object_definition in object_definitions:
        class_name = object_definition.split(":")[0].strip()
        source += "        @abstractmethod\n"
        source += f"        def visit_{class_name.lower()}_{base_class_name.lower()}(self, {base_class_name.lower()}: {class_name}):\n"
        source += "            pass\n\n"

    for object_definition in object_definitions:
        source += generate_type(base_class_name, object_definition) + "\n"

        with open(
                output_dir.rstrip("/") + "/" + base_class_name.lower() + ".py",
                mode="w",
                encoding="UTF-8") as file:
            file.write(source)
    return source

def generate_type(base_class_name: str, object_definition: str) -> str:
    class_name: str = object_definition.split(":")[0].strip()
    members: Optional[str] = None
    if len(object_definition.split(":")) > 1:
        members = object_definition.split(":")[1].strip()

    source = "\n@dataclass\n"
    source += f"class {class_name}({base_class_name}):\n"
    if members is not None:
        source += generate_members(members)

    source += "\n    def accept(self, visitor: " + base_class_name + ".Visitor):\n"
    source += f"        return visitor.visit_{class_name.lower()}_{base_class_name.lower()}(self)\n"

    return source

def generate_members(members: str):
    member_definitions = (member.strip() for member in members.split(";"))
    source: str = ""
    for member_definition in member_definitions:
        member_type = member_definition.split(" ")[0].strip().replace("~", " ")
        member_name = member_definition.split(" ")[1].strip()
        source += f"    {member_name}: {member_type}\n"
    return source


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("USAGE " + sys.argv[0] + " <output_dir>")
        sys.exit(64)

    OUTPUT_DIR = sys.argv[1]

    BASE_CLASS = "Expr"
    OBJECT_DEFINITIONS = [
        "Binary: Expr left; Token operator; Expr right",
        "Call: Expr callee; Token paren; list[Expr] arguments",
        "Unary: Token operator; Expr right",
        "Grouping: Expr expression",
        "Literal: LiteralType value",
        "Ternery: Expr condition; Expr then_expr; Expr else_expr",
        "Variable: Token name",
        "Assign: Token name; Expr value",
        "Logical: Expr left; Token operator; Expr right",
        "Function: list[Token] params; list[stmt.Stmt] body",
        "Get: Expr object; Token name",
        "Set: Expr object; Token name; Expr value",
        "This: Token keyword",
        "Super: Token keyword; Token method; Optional[Token] superclass"
    ]
    IMPORTS = ["from . import stmt"]
    generate_ast(BASE_CLASS, OBJECT_DEFINITIONS, OUTPUT_DIR, IMPORTS)

    BASE_CLASS = "Stmt"
    OBJECT_DEFINITIONS = [
        "Expression: expr.Expr expression",
        "If: expr.Expr condition; Stmt then_branch; Optional[Stmt] else_branch",
        "Print: expr.Expr expression",
        "While: expr.Expr condition; Stmt body",
        "FunDef: Token name; expr.Function function",
        "Var: Token name; Optional[expr.Expr] initializer",
        "Block: list[Stmt] statements",
        "Break: Token keyword",
        "Return: Token keyword; Optional[expr.Expr] value",
        "Class: Token name; list[Variabel] superclasses; list[FunDef] methods; list[FunDef] static_methods"
    ]
    IMPORTS = ["from . import expr"]
    generate_ast(BASE_CLASS, OBJECT_DEFINITIONS, OUTPUT_DIR, IMPORTS)
