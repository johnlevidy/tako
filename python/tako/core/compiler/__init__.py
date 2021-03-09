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
import tako.core.types as pt
from tako.core import sir, ingest
from tako.core.compiler import types, constants, conversions, prefix_namespace
from tako.core.error import Error
from tako.util.qname import QName
from pathlib import Path

from tako.generators.generator import Generator


def compile_proto(
    proto_class: t.Type[pt.Protocol], namespace: str
) -> t.Union[t.List[Error], sir.Protocol]:
    proto = ingest.run(proto_class._proto_proto)
    if isinstance(proto, list):
        return proto

    comp_types = types.compile(proto.name, proto.types, proto.type_order)
    if isinstance(comp_types, list):
        return comp_types

    comp_constants = constants.compile(proto.constants)
    if isinstance(comp_constants, list):
        return comp_constants

    comp_conversions = conversions.compile(
        proto.name, proto.conversions, comp_types.types
    )
    if isinstance(comp_conversions, Error):
        return [comp_conversions]

    return prefix_namespace.prefix(
        sir.Protocol(proto.name, comp_types, comp_constants, comp_conversions),
        QName.from_pyname(namespace),
    )


def generate(
    proto_class: t.Type[pt.Protocol],
    namespace: str,
    out_dir: Path,
    gen: Generator,
    list_outputs: bool,
    args: t.Any,
    output: t.IO,
) -> t.List[str]:

    if list_outputs:
        proto = ingest.run(proto_class._proto_proto)
        if isinstance(proto, list):
            return ["Failed to list outputs due to errors ingestion errors: "] + [
                str(e) for e in proto
            ]
        for path in gen.list_outputs(proto.name, args):
            print(out_dir / path, file=output)
    else:
        result = compile_proto(proto_class, namespace)
        if isinstance(result, list):
            return [str(error) for error in result]

        gen.generate(result, out_dir, args)

    return []
