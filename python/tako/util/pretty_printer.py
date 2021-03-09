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


@dataclasses.dataclass
class PrettyPrinter:
    indent_width: int
    stream: t.IO
    current_indent: int = dataclasses.field(default=0, init=False)
    line_indented: bool = dataclasses.field(default=False, init=False)

    def putln(self, line: str = "") -> None:
        self.put(line, newline=True)

    def put(self, line: str = "", newline: bool = False) -> None:
        if not self.line_indented:
            indent = " " * self.current_indent
        else:
            indent = ""
        if newline:
            self.line_indented = False
        else:
            self.line_indented = True
        print(indent + line, file=self.stream, end="\n" if newline else "")

    def push_indent(self) -> None:
        self.current_indent += self.indent_width

    def pop_indent(self) -> None:
        self.current_indent -= self.indent_width

    def __enter__(self) -> None:
        self.push_indent()

    def __exit__(self, exc_type: t.Any, exc_value: t.Any, traceback: t.Any) -> None:
        self.pop_indent()
