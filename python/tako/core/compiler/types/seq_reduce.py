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
from tako.core.compiler.types import mir
from tako.util.qname import QName
from tako.core.compiler.types.size import SizeCalculator, RootSizeResult
import tako.core.size_types as st
from tako.core.internal_error import InternalError


def run(
    types: t.Dict[QName, mir.RootType],
    type_order: t.List[QName],
    size_map: t.Dict[QName, RootSizeResult],
) -> None:
    for name in type_order:
        replacement = types[name].accept(SeqReduce(size_map))
        if replacement is not None:
            types[name] = replacement


@dataclasses.dataclass
class SeqReduce(mir.RootTypeVisitor[t.Optional[mir.Struct]]):
    size_map: t.Dict[QName, RootSizeResult]

    def visit_struct(self, root: mir.Struct) -> t.Optional[mir.Struct]:
        return mir.Struct(
            root.name,
            {
                fname: ftype.accept(SeqReduceField(self.size_map))
                for fname, ftype in root.fields.items()
            },
        )

    def visit_variant(self, root: mir.Variant) -> t.Optional[mir.Struct]:
        return None

    def visit_enum(self, root: mir.Enum) -> t.Optional[mir.Struct]:
        return None


@dataclasses.dataclass
class SeqReduceField(mir.SeqTypeVisitor[mir.Type]):
    size_map: t.Dict[QName, RootSizeResult]

    def visit_int(self, type_: mir.Int) -> mir.Type:
        return type_

    def visit_float(self, type_: mir.Float) -> mir.Type:
        return type_

    def visit_seq(self, type_: mir.Seq) -> mir.Type:
        inner_reduced = type_.inner.accept(self)
        inner_size = type_.inner.accept(SizeCalculator(self.size_map))
        return inner_size.accept(InnerSizeVisitor(inner_reduced, type_.length))

    def visit_unbound_seq(self, type_: mir.UnboundSeq) -> mir.Type:
        raise InternalError()

    def visit_detached_variant(self, type_: mir.DetachedVariant) -> mir.Type:
        return type_

    def visit_virtual(self, type_: mir.Virtual) -> mir.Type:
        return mir.Virtual(type_.inner.accept(self))

    def visit_ref(self, type_: mir.Ref) -> mir.Type:
        return type_


@dataclasses.dataclass
class InnerSizeVisitor(st.SizeVisitor[mir.Type]):
    inner_reduced: mir.Type
    outer_length: mir.Length

    def visit_constant(self, size: st.Constant) -> mir.Type:
        return self.outer_length.accept(OuterLengthVisitor(self.inner_reduced))

    def visit_dynamic(self, size: st.Dynamic) -> mir.Type:
        return mir.List(self.inner_reduced, self.outer_length)


@dataclasses.dataclass
class OuterLengthVisitor(mir.LengthVisitor[mir.Type]):
    inner_reduced: mir.Type

    def visit_fixed_length(self, length: mir.FixedLength) -> mir.Type:
        return mir.Array(self.inner_reduced, length.length)

    def visit_variable_length(self, length: mir.VariableLength) -> mir.Type:
        return mir.Vector(self.inner_reduced, length.length)
