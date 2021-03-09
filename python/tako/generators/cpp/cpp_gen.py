# Copyright 2020 Jacob Glueck
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import typing as t
import enum
import dataclasses
import textwrap
from tako.util.pretty_printer import PrettyPrinter
from tako.core.internal_error import QuirkAbstractDataclass


@dataclasses.dataclass
class Node:
    def pretty_printer(self, printer: PrettyPrinter) -> None:
        raise QuirkAbstractDataclass()


@dataclasses.dataclass
class Include:
    fname: str
    system: bool = False

    def __str__(self) -> str:
        if self.system:
            return f"<{self.fname}>"
        else:
            return f'"{self.fname}"'


@dataclasses.dataclass
class File(Node):
    includes: t.List[Include]
    body: Node
    pragma_once: bool = False

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        if self.pragma_once:
            printer.putln(f"#pragma once")
            printer.putln()
        for include in self.includes:
            printer.putln(f"#include {include}")
        if self.includes:
            printer.putln()
        self.body.pretty_printer(printer)


@dataclasses.dataclass
class Namespace(Node):
    name: str
    body: Node

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        printer.putln(f"namespace {self.name} {{")
        self.body.pretty_printer(printer)
        printer.putln("}")


@enum.unique
class Visibility(enum.Enum):
    PUBLIC = enum.auto()
    PROTECTED = enum.auto()
    PRIVATE = enum.auto()

    def __repr__(self) -> str:
        return self.name.lower()

    def __str__(self) -> str:
        return self.name.lower()


@dataclasses.dataclass
class Section(Node):
    parts: t.List[Node]

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        for part in self.parts:
            part.pretty_printer(printer)


@dataclasses.dataclass
class Class(Node):
    name: str
    bases: t.List[t.Tuple[Visibility, str]]
    sections: t.List[t.Tuple[Visibility, Section]]
    template_args: t.Optional[str] = None
    is_struct: bool = False

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        if self.template_args is not None:
            printer.putln(f"template <{self.template_args}>")
        if self.is_struct:
            ctype = "struct"
        else:
            ctype = "class"
        printer.put(f"{ctype} {self.name}")
        if self.bases:
            printer.put(" : ")
            printer.put(
                ", ".join([f"{visibility} {name}" for visibility, name in self.bases])
            )
        printer.putln(" {")
        for visibility, section in self.sections:
            if section.parts:
                printer.putln(f"{visibility}:")
                with printer:
                    section.pretty_printer(printer)
        printer.putln("};")


@dataclasses.dataclass
class Type:
    name: str


@dataclasses.dataclass
class Function(Node):
    name: str
    params: t.List[t.Tuple[Type, str]]
    return_type: Type
    body: Node
    static: bool = False
    const: bool = False

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        if self.static:
            printer.put("static ")
        param_string = ", ".join(
            [f"{type_.name} {name}" for type_, name in self.params]
        )
        const_string = "const " if self.const else ""
        printer.putln(
            f"{self.return_type.name} {self.name}({param_string}) {const_string}{{"
        )
        with printer:
            self.body.pretty_printer(printer)
        printer.putln("}")


@dataclasses.dataclass
class If(Node):
    guard: str
    true_block: Node
    false_block: t.Optional[Node]

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        printer.putln(f"if ({self.guard}) {{")
        with printer:
            self.true_block.pretty_printer(printer)
        printer.put("}")
        if self.false_block is None:
            printer.putln("")
        else:
            printer.put(" else ")
            self.false_block.pretty_printer(printer)


@dataclasses.dataclass
class Raw(Node):
    lines: t.List[str]

    def __init__(self, raw: str) -> None:
        self.lines = textwrap.dedent(raw).splitlines()

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        for line in self.lines:
            printer.putln(line)
