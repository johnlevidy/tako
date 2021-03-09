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
import dataclasses
import textwrap
from tako.util.pretty_printer import PrettyPrinter
from tako.core.internal_error import QuirkAbstractDataclass


@dataclasses.dataclass
class Node:
    def pretty_printer(self, printer: PrettyPrinter) -> None:
        raise QuirkAbstractDataclass()


@dataclasses.dataclass
class Section(Node):
    parts: t.Sequence[Node]

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        for part in self.parts:
            part.pretty_printer(printer)


@dataclasses.dataclass
class Class(Node):
    name: str
    body: Node
    static: bool = False

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        if self.static:
            static_str = " static"
        else:
            static_str = ""
        printer.putln(f"public{static_str} class {self.name} {{")
        with printer:
            self.body.pretty_printer(printer)
        printer.putln("}")


@dataclasses.dataclass
class Type:
    name: str


@dataclasses.dataclass
class Function(Node):
    visibility: str
    name: str
    params: t.List[t.Tuple[Type, str]]
    return_type: Type
    body: Node
    static: bool = False
    throws: t.List[str] = dataclasses.field(default_factory=list)

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        if self.static:
            printer.put("static ")
        param_string = ", ".join(
            [f"{type_.name} {name}" for type_, name in self.params]
        )
        if self.throws:
            throws_string = "throws " + " ".join(self.throws) + " "
        else:
            throws_string = ""

        printer.putln(
            f"{self.visibility} {self.return_type.name} {self.name}({param_string}) {throws_string}{{"
        )
        with printer:
            self.body.pretty_printer(printer)
        printer.putln("}")


@dataclasses.dataclass
class Raw(Node):
    lines: t.List[str]

    def __init__(self, raw: str) -> None:
        self.lines = textwrap.dedent(raw).splitlines()

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        for line in self.lines:
            printer.putln(line)
