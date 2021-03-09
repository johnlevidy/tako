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
import abc
import dataclasses
import textwrap
from tako.util.pretty_printer import PrettyPrinter


class Node(abc.ABC):
    def pretty_printer(self, printer: PrettyPrinter) -> None:
        ...


@dataclasses.dataclass
class Section(Node):
    parts: t.List[Node]

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        for part in self.parts:
            part.pretty_printer(printer)


@dataclasses.dataclass
class Class(Node):
    name: str
    body: Node
    decorator: t.Optional[str] = None

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        if self.decorator is not None:
            printer.putln(self.decorator)
        printer.putln(f"class {self.name}:")
        with printer:
            self.body.pretty_printer(printer)


@dataclasses.dataclass
class Type:
    name: str


@dataclasses.dataclass
class Function(Node):
    name: str
    params: t.List[t.Tuple[t.Optional[Type], str]]
    return_type: Type
    body: Node
    decorator: t.Optional[str] = None

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        def type_suffix(x: t.Optional[Type]) -> str:
            if x is None:
                return ""
            else:
                return f": {x.name}"

        param_string = ", ".join(
            [f"{name}{type_suffix(type_)}" for type_, name in self.params]
        )
        if self.decorator is not None:
            printer.putln(self.decorator)
        printer.putln(f"def {self.name}({param_string}) -> {self.return_type.name}:")
        with printer:
            self.body.pretty_printer(printer)


@dataclasses.dataclass
class Raw(Node):
    lines: t.List[str]

    def __init__(self, raw: str) -> None:
        self.lines = textwrap.dedent(raw).splitlines()

    def pretty_printer(self, printer: PrettyPrinter) -> None:
        for line in self.lines:
            printer.putln(line)
