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
from tako.core.compiler import types
from tako.core.compiler.conversions import mir
from tako.util.qname import QName
from tako.util.cast import unwrap
from tako.core.error import Error
from tako.util.graph import Graph


def resolve(convs: Graph[QName, mir.RootConversion]) -> t.Optional[Error]:
    for src, target in list(convs.links()):
        expanded = unwrap(convs.get(src, target)).accept(Resolver(convs))
        if isinstance(expanded, Error):
            return expanded
        convs.put(src, target, expanded)
    return None


@dataclasses.dataclass
class Resolver(
    mir.RootConversionVisitor[t.Union[Error, mir.RootConversion]],
    mir.ConversionVisitor[t.Union[Error, mir.Conversion]],
    mir.FieldConversionVisitor[t.Union[Error, mir.FieldConversion]],
):
    convs: Graph[QName, mir.RootConversion]

    def visit_enum_conversion(
        self, conv: mir.EnumConversion
    ) -> t.Union[Error, mir.RootConversion]:
        return conv

    def visit_struct_conversion(
        self, conv: mir.StructConversion
    ) -> t.Union[Error, mir.RootConversion]:
        new_mapping = {}

        for fname, fc in conv.mapping.items():
            resolved_fc = fc.accept(self)
            if isinstance(resolved_fc, Error):
                return resolved_fc
            else:
                new_mapping[fname] = resolved_fc

        return mir.StructConversion(conv.protocol, conv.src, conv.target, new_mapping)

    def visit_variant_conversion(
        self, conv: mir.VariantConversion
    ) -> t.Union[Error, mir.RootConversion]:
        new_mapping = []

        for vvm in conv.mapping:
            target: t.Optional[mir.VariantValueConversion]
            if vvm.target is not None:
                resolved = vvm.target.conversion.accept(self)
                if isinstance(resolved, Error):
                    return resolved
                target = mir.VariantValueConversion(vvm.target.target, resolved)
            else:
                target = None
            new_mapping.append(mir.VariantValueMapping(vvm.src, target))

        return mir.VariantConversion(conv.protocol, conv.src, conv.target, new_mapping)

    def visit_identity_conversion(
        self, conv: mir.IdentityConversion
    ) -> t.Union[Error, mir.Conversion]:
        return conv

    def visit_unresolved_conversion(
        self, conv: mir.UnresolvedConversion
    ) -> t.Union[Error, mir.Conversion]:
        # TODO: handle convs for unammed types (integers and list-like things)
        # (beyond the identity conv that is)
        if conv.src == conv.target:
            # TODO: this isn't strictly true for seq with a field reference length.
            # If the position of the length field changes (but not the name),
            # that's not OK. Similiar to the DetachedVariant case below.
            # TODO: also unclear what happens to virtual fields.
            return mir.IdentityConversion(conv.src, conv.target)
        elif isinstance(conv.src, types.lir.RootType) and isinstance(
            conv.target, types.lir.RootType
        ):
            maybe = self.convs.get(conv.src.name, conv.target.name)
            if maybe is None:
                return Error(
                    f"No conversion found from {conv.src.name} -> {conv.target.name}"
                )
            else:
                return mir.ConversionRef(conv.src, conv.target)
        elif isinstance(conv.src, types.lir.DetachedVariant) and isinstance(
            conv.target, types.lir.DetachedVariant
        ):
            # TODO: figure out what happens when the tag field is changed.
            # It's kind of OK because in built types the tag field isn't there
            # and doesn't matter. But for view types it matters.
            # Probably just need to track this, and instead of returning
            # an unresolved conversion here, return a
            # DetachedVariantConversion, which has the before and after tag fields,
            # along with the resolved conversion.
            # Then the conversion property checker will at least be aware of this
            # and can handle it.
            return self.visit_unresolved_conversion(
                mir.UnresolvedConversion(conv.src.variant, conv.target.variant)
            )
        else:
            return Error(f"No conversion found from {conv.src} -> {conv.target}")

    def visit_conversion_ref(
        self, conv: mir.ConversionRef
    ) -> t.Union[Error, mir.Conversion]:
        return conv

    def visit_int_default_field_conversion(
        self, conv: mir.IntDefaultFieldConversion
    ) -> t.Union[Error, mir.FieldConversion]:
        return conv

    def visit_enum_default_field_conversion(
        self, conv: mir.EnumDefaultFieldConversion
    ) -> t.Union[Error, mir.FieldConversion]:
        return conv

    def visit_transform_field_conversion(
        self, conv: mir.TransformFieldConversion
    ) -> t.Union[Error, mir.FieldConversion]:
        resolved = conv.conversion.accept(self)
        if isinstance(resolved, Error):
            return resolved
        return mir.TransformFieldConversion(conv.src_field, resolved)
