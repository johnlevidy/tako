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
from tako.core.internal_error import InternalError
import tako.core.size_types as st


def run(
    types: t.Dict[QName, mir.RootType], type_order: t.List[QName]
) -> t.Dict[QName, RootSizeResult]:

    result: t.Dict[QName, RootSizeResult] = {}
    for name in type_order:
        result[name] = types[name].accept(RootSizeCalculator(types, result))

    return result


@dataclasses.dataclass(frozen=True)
class OffsetResult:
    offset_map: t.Dict[str, st.Offset]
    tail_offset: st.Offset


@dataclasses.dataclass(frozen=True)
class RootSizeResult:
    size: st.Size
    offset: t.Optional[OffsetResult]


@dataclasses.dataclass
class RootSizeCalculator(mir.RootTypeVisitor[RootSizeResult]):
    types: t.Dict[QName, mir.RootType]
    size_map: t.Dict[QName, RootSizeResult]

    def visit_struct(self, root: mir.Struct) -> RootSizeResult:
        current_offset = st.Offset.zero()
        offsets = {}
        for fname, ftype in root.fields.items():
            offsets[fname] = current_offset
            fsize = ftype.accept(SizeCalculator(self.size_map))
            current_offset = current_offset.add(fname, fsize)
        return RootSizeResult(
            current_offset.as_size(), OffsetResult(offsets, current_offset)
        )

    def visit_variant(self, root: mir.Variant) -> RootSizeResult:
        target_size: t.Optional[st.Constant] = None
        for sr in root.types():
            size = self.size_map[sr.name].size
            if not isinstance(size, st.Constant):
                return RootSizeResult(st.Dynamic(), None)
            if target_size is None:
                target_size = size
            elif target_size != size:
                return RootSizeResult(st.Dynamic(), None)

        # If target_size is still none, then
        # there are no variants, so this variant has 0 size.
        return RootSizeResult(target_size or st.Constant(0), None)

    def visit_enum(self, root: mir.Enum) -> RootSizeResult:
        return RootSizeResult(
            root.underlying_type.accept(SizeCalculator(self.size_map)), None
        )


@dataclasses.dataclass
class SizeCalculator(mir.TypeVisitor[st.Size]):
    size_map: t.Dict[QName, RootSizeResult]

    def visit_int(self, type_: mir.Int) -> st.Size:
        return st.Constant(type_.width)

    def visit_float(self, type_: mir.Float) -> st.Size:
        return st.Constant(type_.width)

    def visit_seq(self, type_: mir.Seq) -> st.Size:
        inner_size = type_.inner.accept(self)
        if isinstance(inner_size, st.Constant) and isinstance(
            type_.length, mir.FixedLength
        ):
            return st.Constant(inner_size.value * type_.length.length)
        else:
            return st.Dynamic()

    def visit_unbound_seq(self, type_: mir.UnboundSeq) -> st.Size:
        raise InternalError()

    # This is so we can compute the size in fuse.py after seq_reduce
    def visit_array(self, type_: mir.Array) -> st.Size:
        return mir.Seq(type_.inner, mir.FixedLength(type_.length)).accept(self)

    def visit_vector(self, type_: mir.Vector) -> st.Size:
        return mir.Seq(type_.inner, mir.VariableLength(type_.length)).accept(self)

    def visit_list(self, type_: mir.List) -> st.Size:
        return mir.Seq(type_.inner, type_.length).accept(self)

    def visit_detached_variant(self, type_: mir.DetachedVariant) -> st.Size:
        return type_.variant.accept(self)

    def visit_virtual(self, type_: mir.Virtual) -> st.Size:
        # The whole thing has a size of 0, because it takes no space in the
        # parent struct.
        # But size the inner types because they need to be sized so the
        # virtual parser can parse them
        return st.Constant(0)

    def visit_ref(self, type_: mir.Ref) -> st.Size:
        return self.size_map[type_.name].size
