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
import tako.core.types as pt
from tako.core.compiler.types import mir
from tako.util.qname import QName
from tako.util.cast import checked_cast


def lower(types: t.Dict[QName, pt.RootType]) -> t.Dict[QName, mir.RootType]:
    return {name: type_.accept_rtv(RootLower()) for name, type_ in types.items()}


@dataclasses.dataclass
class RootLower(pt.RootTypeVisitor[mir.RootType]):
    def visit_enum_def(self, type_: pt.EnumDef) -> mir.RootType:
        return mir.Enum(
            type_.qualified_name(),
            checked_cast(mir.Int, type_.underlying.accept(Lower())),
            {name: checked_cast(int, value) for name, value in type_.variants.items()},
        )

    def visit_struct_def(self, type_: pt.StructDef) -> mir.RootType:
        return mir.Struct(
            type_.qualified_name(),
            {name: type_.accept(Lower()) for name, type_ in type_.fields.items()},
        )

    def visit_variant_def(self, type_: pt.VariantDef) -> mir.RootType:
        return mir.FixedVariant(
            type_.qualified_name(),
            checked_cast(mir.Int, type_.tag_type.accept(Lower())),
            {
                checked_cast(mir.StructRef, struct.accept(Lower())): value
                for struct, value in type_.variants.items()
            },
        )

    def visit_hash_variant_def(self, type_: pt.HashVariantDef) -> mir.RootType:
        return mir.HashVariant(
            type_.qualified_name(),
            checked_cast(mir.Int, type_.tag_type.accept(Lower())),
            set(
                [
                    checked_cast(mir.StructRef, struct.accept(Lower()))
                    for struct in type_.hash_types
                ]
            ),
        )


@dataclasses.dataclass
class Lower(pt.TypeVisitor[mir.Type]):
    def visit_int(self, type_: pt.Int) -> mir.Type:
        return mir.Int(type_.width, type_.sign, type_.endianness)

    def visit_float(self, type_: pt.Float) -> mir.Type:
        return mir.Float(type_.width, type_.endianness)

    def visit_seq(self, type_: pt.Seq) -> mir.Type:
        li = type_.inner.accept(self)

        if isinstance(type_.length, pt.Int):
            return mir.UnboundSeq(li, checked_cast(mir.Int, type_.length.accept(self)))
        elif isinstance(type_.length, pt.StructPath):
            return mir.Seq(
                li, mir.VariableLength(mir.FieldReference(type_.length.name))
            )
        else:
            return mir.Seq(li, mir.FixedLength(type_.length))

    def visit_detached_variant(self, type_: pt.DetachedVariant) -> mir.Type:
        return mir.DetachedVariant(
            mir.VariantRef(type_.variant.qualified_name()),
            mir.FieldReference(type_.tag.name),
        )

    def visit_virtual(self, type_: pt.Virtual) -> mir.Type:
        return mir.Virtual(type_.inner.accept(self))

    def visit_enum_def(self, type_: pt.EnumDef) -> mir.Type:
        return mir.EnumRef(type_.qualified_name())

    def visit_struct_def(self, type_: pt.StructDef) -> mir.Type:
        return mir.StructRef(type_.qualified_name())

    def visit_variant_def(self, type_: pt.VariantDef) -> mir.Type:
        return mir.VariantRef(type_.qualified_name())

    def visit_hash_variant_def(self, type_: pt.HashVariantDef) -> mir.Type:
        return mir.VariantRef(type_.qualified_name())
