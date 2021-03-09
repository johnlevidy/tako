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
from pathlib import Path
import argparse
import importlib
import sys
import tako.core.types as pt
from tako.core.compiler import generate

from tako.generators.cpp.cpp import CppGenerator

from tako.generators.python.python import PythonGenerator

from tako.generators.java.java import JavaGenerator
from tako.generators.lsir.lsir import LsirGenerator


def get_proto(python_name: str) -> t.Union[str, t.Type[pt.Protocol]]:
    parts = python_name.rsplit(".", 1)
    if len(parts) != 2:
        return f"Illegal proto name: {python_name}"

    module, cls = parts

    try:
        live_module = importlib.import_module(module)
    except Exception as e:
        return f"Failed to import: {python_name}: {e}"

    if not hasattr(live_module, cls):
        return f"Module {module} has no protocol {cls}"

    live_cls = getattr(live_module, cls)
    if not issubclass(live_cls, pt.Protocol):
        return f"Not a protocol class: {live_cls}"

    return live_cls


generators = {
    "cpp": CppGenerator(),
    "lsir": LsirGenerator(),
    "python": PythonGenerator(),
    "java": JavaGenerator(),
}
# TODO add a custom generator which takes a module path as input


def generate_subcmd(args: t.Any, output: t.IO) -> int:
    result = get_proto(args.proto)
    if isinstance(result, str):
        print(result, file=output)
        return 1
    else:
        proto = result

    errors = generate(
        proto,
        args.namespace,
        Path(args.out_dir),
        args.gen,
        args.list_outputs,
        args,
        output,
    )
    if errors:
        for error in errors:
            print(error, file=output)
        return 1

    return 0


def main(argv: t.List[str], output: t.IO) -> int:
    parser = argparse.ArgumentParser(description="Generate protocols")
    subcmd = parser.add_subparsers(dest="subcmd", required=True)

    generator_parser = subcmd.add_parser("generate")
    generator_parser.set_defaults(subcmd=generate_subcmd)

    generator_parser.add_argument(
        "--namespace",
        help="prepend a namespace to everything in the protocol. Namespace is . seperated.",
        default="",
    )
    generator_parser.add_argument(
        "--list-outputs",
        action="store_true",
        help="List the paths of files that will be generated, but do not generate them",
    )
    generator_parser.add_argument("out_dir", help="output directory")
    generator_parser.add_argument("proto", help="protocol python classes")
    generator_subparsers = generator_parser.add_subparsers(
        dest="generator", required=True
    )
    for generator_name, generator in generators.items():
        subparser = generator_subparsers.add_parser(generator_name)
        generator.configure_parser(subparser)
        subparser.set_defaults(gen=generator)

    args = parser.parse_args(argv)
    return args.subcmd(args, output)


def wrapper_main() -> None:
    sys.exit(main(sys.argv[1:], sys.stdout))


if __name__ == "__main__":
    wrapper_main()
