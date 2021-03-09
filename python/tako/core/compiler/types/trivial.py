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


def run(
    types: t.Dict[QName, mir.RootType], type_order: t.List[QName]
) -> t.Dict[QName, bool]:
    result: t.Dict[QName, bool] = {}
    for name in type_order:
        result[name] = types[name].accept(CheckTrivial(result))
    return result


@dataclasses.dataclass
class CheckTrivial(mir.RootTypeVisitor[bool]):
    tmap: t.Dict[QName, bool]

    def visit_struct(self, root: mir.Struct) -> bool:
        u = True
        for fname, ftype in root.fields.items():
            uf = ftype.accept(CheckTrivialField(self.tmap))
            u = u and uf
        return u

    def visit_variant(self, root: mir.Variant) -> bool:
        return False

    def visit_enum(self, root: mir.Enum) -> bool:
        return False


@dataclasses.dataclass
class CheckTrivialField(mir.LoweredTypeVisitor[bool]):
    tmap: t.Dict[QName, bool]

    def visit_int(self, type_: mir.Int) -> bool:
        return True

    def visit_float(self, type_: mir.Float) -> bool:
        return True

    def visit_array(self, type_: mir.Array) -> bool:
        return type_.inner.accept(self)

    def visit_vector(self, type_: mir.Vector) -> bool:
        return False

    def visit_list(self, type_: mir.List) -> bool:
        return False

    def visit_detached_variant(self, type_: mir.DetachedVariant) -> bool:
        return False

    def visit_virtual(self, type_: mir.Virtual) -> bool:
        return False

    def visit_ref(self, type_: mir.Ref) -> bool:
        return self.tmap[type_.name]
