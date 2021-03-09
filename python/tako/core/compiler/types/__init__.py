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
from tako.core.compiler.types import (
    lower,
    definition_order,
    check_stuff,
    variant_expand,
    seq_expand,
    master_fields,
    hash_expand,
    size,
    enum_range,
    trivial,
    seq_reduce,
    own,
    fuse,
    lir,
)
from tako.core.error import Error
from tako.util.qname import QName

# type_order is ordered in topological order with leaves first
def compile(
    proto_name: QName, types: t.Dict[QName, pt.RootType], type_order: t.List[QName]
) -> t.Union[t.List[Error], lir.ProtocolTypes]:
    lowered = lower.lower(types)

    checks = [definition_order.run, check_stuff.run, variant_expand.run, seq_expand.run]
    for check in checks:
        errors = check(lowered, type_order)
        if errors:
            return errors

    master_field_map = master_fields.run(lowered, type_order)
    if isinstance(master_field_map, list):
        return master_field_map

    digest_map = hash_expand.run(lowered, type_order)
    if isinstance(digest_map, list):
        return digest_map

    size_map = size.run(lowered, type_order)
    enum_ranges = enum_range.run(lowered, type_order)
    seq_reduce.run(lowered, type_order, size_map)
    tmap = trivial.run(lowered, type_order)
    own_types, external_protocols = own.run(proto_name, type_order)

    return fuse.run(
        lowered,
        type_order,
        master_field_map,
        digest_map,
        size_map,
        enum_ranges,
        tmap,
        own_types,
        external_protocols,
    )
