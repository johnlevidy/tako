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
from tako.core.compiler import types
from tako.core.compiler.conversions import (
    lower,
    expand,
    resolve,
    dependencies,
    properties,
    fuse,
    lir,
)
from tako.core.error import Error
from tako.util.qname import QName
from tako.util.graph import Graph, Cycle
from tako.util.cast import unwrap

# type_order is ordered in topological order with leaves first
def compile(
    proto_name: QName,
    conversions: Graph[QName, pt.ResolvedConversion],
    types: t.Dict[QName, types.lir.RootType],
) -> t.Union[Error, lir.ProtocolConversions]:

    lowered = lower.lower(conversions, types)
    if isinstance(lowered, Error):
        return lowered

    checks = [expand.expand, resolve.resolve]
    for check in checks:
        errors = check(lowered)
        if errors:
            return errors

    dep_graph = dependencies.build_dependency_graph(lowered)
    order = dep_graph.toposort()

    if isinstance(order, Cycle):
        return Error(
            f"Cycle in conversion dependency graph involving: {order.vertices}"
        )

    cprops = properties.compute(lowered)
    fused = fuse.fuse(lowered, cprops)

    own_conversions: t.List[lir.RootConversion] = []
    # The order starts with every conversion at the top of the dependency graph
    # (conversions which are dependent on other conversions)
    for handle in reversed(order):
        conversion = unwrap(fused.get(handle.src, handle.target))
        if conversion.protocol == proto_name:
            own_conversions.append(conversion)

    return lir.ProtocolConversions(fused, own_conversions)
