"""
Provides the function generate_ast to generate a python source code
file containing auto generated classes for the abstract syntax tree.
"""
def generate_ast(base_class_name: str, object_definitions: list[str]) -> str:
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
from .lexer import Token

class """+base_class_name+"""(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor):
        pass
    
"""
    for object_definition in object_definitions:
        source += generate_type(base_class_name, object_definition) + "\n"

    source += "\nclass Visitor(ABC):\n"
    for object_definition in object_definitions:
        class_name = object_definition.split(":")[0].strip()
        source += "    @abstractmethod\n"
        source += f"    def visit_{class_name.lower()}_{base_class_name.lower()}(self, {base_class_name.lower()}: {class_name}):\n"
        source += "        pass\n\n"
    return source

def generate_type(base_class_name: str, object_definition: str) -> str:
    class_name: str = object_definition.split(":")[0].strip()
    members: str = object_definition.split(":")[1].strip()

    source = "@dataclass\n"
    source += f"class {class_name}({base_class_name}):\n"
    source += generate_members(members)
    source += "\n    def accept(self, visitor: Visitor):\n"
    source += f"        return visitor.visit_{class_name.lower()}_{base_class_name.lower()}(self)\n"

    return source

def generate_members(members: str):
    member_definitions = (member.strip() for member in members.split(","))
    source: str = ""
    for member_definition in member_definitions:
        member_type = member_definition.split(" ")[0].strip()
        member_name = member_definition.split(" ")[1].strip()
        source += f"    {member_name}: {member_type}\n"
    return source


if __name__ == "__main__":
    BASE_CLASS = "Expr"
    OBJECT_DEFINITIONS = [
        "Binary: Expr left, Token operator, Expr right",
        "Unary: Token operator, Expr right",
        "Grouping: Expr expression",
        "Literal: str|float value"
    ]
    print(generate_ast(BASE_CLASS, OBJECT_DEFINITIONS))