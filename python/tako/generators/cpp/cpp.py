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

from __future__ import annotations

import typing as t
import argparse
from pathlib import Path
from tako.generators.cpp import core, json
from tako.generators.generator import Generator
from tako.util.qname import QName
from tako.core.sir import Protocol
from tako.generators.cpp.types import (
    relative_path,
    wrap_in_namespace,
    protocol_namespace,
)
from tako.generators.cpp import cpp_gen as cg
from tako.util.pretty_printer import PrettyPrinter


class CppGenerator(Generator):
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--json", action="store_true")

    def list_outputs(
        self, proto_qname: QName, args: t.Any
    ) -> t.Generator[Path, None, None]:
        yield main_file(proto_qname)
        yield core.out_relative_path(proto_qname)
        if args.json:
            yield json.out_relative_path(proto_qname)

    def generate_into(self, proto: Protocol, out_dir: Path, args: t.Any) -> None:
        includes = [cg.Include(str(core.out_relative_path(proto.name)))]
        core.generate(proto, out_dir)
        if args.json:
            json.generate(proto, out_dir)
            includes.append(cg.Include(str(json.out_relative_path(proto.name))))

        with (out_dir / main_file(proto.name)).open("w") as main:
            cg.File(
                includes=includes,
                body=wrap_in_namespace(protocol_namespace(proto.name), cg.Raw("")),
            ).pretty_printer(PrettyPrinter(4, main))


def main_file(qname: QName) -> Path:
    return relative_path(qname)
