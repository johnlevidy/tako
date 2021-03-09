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
from tako.core.compiler.types import lir
from tako.core.compiler.conversions import mir
from tako.util.qname import QName
from tako.util.cast import checked_cast
from tako.core.internal_error import InternalError
from tako.util.graph import Graph
from tako.core.error import Error

T = t.TypeVar("T")


def lower(
    conversions: Graph[QName, pt.ResolvedConversion], types: t.Dict[QName, lir.RootType]
) -> t.Union[Error, Graph[QName, mir.RootConversion]]:
    result: Graph[QName, mir.RootConversion] = Graph()
    for src, target, conversion in conversions:
        lowered = conversion.inner.accept(ConversionLower(conversion.protocol, types))
        if isinstance(lowered, Error):
            return lowered
        result.put(src, target, lowered)
    return result


@dataclasses.dataclass
class ConversionLower(pt.ConversionVisitor[t.Union[mir.RootConversion, Error]]):
    protocol: QName
    types: t.Dict[QName, lir.RootType]

    def visit_no_conversion(
        self, conversion: pt.NoConversion
    ) -> t.Union[mir.RootConversion, Error]:
        raise InternalError()

    def get_as(self, type_: t.Type[T], rt: pt.RootType) -> T:
        return checked_cast(type_, self.types[rt.qualified_name()])

    def get_src_target(self, type_: t.Type[T], rt: pt.Conversion) -> t.Tuple[T, T]:
        return (self.get_as(type_, rt.src), self.get_as(type_, rt.target))

    def visit_enum_conversion(
        self, conversion: pt.EnumConversion
    ) -> t.Union[mir.RootConversion, Error]:
        src, target = self.get_src_target(lir.Enum, conversion)
        mapping = []

        for src_ev, target_ev in conversion.mapping.items():
            if src_ev.src is not conversion.src:
                return Error(
                    f"{src_ev} not from src enum: {conversion.src} (from: {src_ev.src})"
                )
            if target_ev is not None and target_ev.src is not conversion.target:
                return Error(
                    f"{target_ev} not from target enum: {conversion.target} (from: {target_ev.src})"
                )

            src_ev_l = mir.EnumValue(src_ev.name, src_ev.value)
            target_ev_l = None
            if target_ev is not None:
                target_ev_l = mir.EnumValue(target_ev.name, target_ev.value)
            mapping.append(mir.EnumValueMapping(src_ev_l, target_ev_l))

        return mir.EnumConversion(
            protocol=self.protocol, src=src, target=target, mapping=mapping
        )

    def visit_struct_conversion(
        self, conversion: pt.StructConversion
    ) -> t.Union[mir.RootConversion, Error]:
        src, target = self.get_src_target(lir.Struct, conversion)
        mapping: t.Dict[str, mir.FieldConversion] = {}
        for target_fr, field_conversion in conversion.mapping.items():
            if target_fr.src is not conversion.target:
                return Error(
                    f"{target_fr} not from target struct: {conversion.target} (from: {target_fr.src})"
                )
            if isinstance(field_conversion, pt.EnumValue):
                mapping[target_fr.name] = mir.EnumDefaultFieldConversion(
                    self.get_as(lir.Enum, field_conversion.src),
                    mir.EnumValue(field_conversion.name, field_conversion.value),
                )
            elif isinstance(field_conversion, int):
                mapping[target_fr.name] = mir.IntDefaultFieldConversion(
                    # Infer the int type from the target field type
                    checked_cast(lir.Int, target.fields[target_fr.name].type_),
                    field_conversion,
                )
            else:
                if field_conversion.src is not conversion.src:
                    return Error(
                        f"{field_conversion} not from source struct: {conversion.src} (from: {field_conversion.src})"
                    )
                mapping[target_fr.name] = mir.TransformFieldConversion(
                    field_conversion.name,
                    mir.UnresolvedConversion(
                        src.fields[field_conversion.name].type_,
                        target.fields[target_fr.name].type_,
                    ),
                )

        return mir.StructConversion(
            protocol=self.protocol, src=src, target=target, mapping=mapping
        )

    def visit_variant_conversion(
        self, conversion: pt.VariantConversion
    ) -> t.Union[mir.RootConversion, Error]:
        src, target = self.get_src_target(lir.Variant, conversion)
        mapping = []

        for src_sd, target_sd in conversion.mapping.items():
            src_struct = self.get_as(lir.Struct, src_sd)

            if src_struct not in src.tags:
                return Error(f"src_struct {src_struct} not in {src}")
            src_vv = mir.VariantValue(src_struct, src.tags[src_struct])

            target_vvc: t.Optional[mir.VariantValueConversion]
            if target_sd is not None:
                target_struct = self.get_as(lir.Struct, target_sd)
                if target_struct not in target.tags:
                    return Error(f"target_struct {target_struct} not in {target}")
                target_vvc = mir.VariantValueConversion(
                    mir.VariantValue(target_struct, target.tags[target_struct]),
                    mir.UnresolvedConversion(src_struct, target_struct),
                )
            else:
                target_vvc = None

            mapping.append(mir.VariantValueMapping(src_vv, target_vvc))

        return mir.VariantConversion(
            protocol=self.protocol, src=src, target=target, mapping=mapping
        )
