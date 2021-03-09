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
import dataclasses
from tako.core.compiler.types import mir
from tako.util.qname import QName
from tako.util.ranges import Range, find_ranges


def run(
    types: t.Dict[QName, mir.RootType], type_order: t.List[QName]
) -> t.Dict[QName, t.List[Range]]:

    result: t.Dict[QName, t.List[Range]] = {}
    for name in type_order:
        ranges = types[name].accept(EnumRangeCalculator())
        if ranges is not None:
            result[name] = ranges
    return result


@dataclasses.dataclass
class EnumRangeCalculator(mir.RootTypeVisitor[t.Optional[t.List[Range]]]):
    def visit_struct(self, root: mir.Struct) -> t.Optional[t.List[Range]]:
        return None

    def visit_variant(self, root: mir.Variant) -> t.Optional[t.List[Range]]:
        return None

    def visit_enum(self, root: mir.Enum) -> t.Optional[t.List[Range]]:
        return find_ranges(list(root.variants.values()))
