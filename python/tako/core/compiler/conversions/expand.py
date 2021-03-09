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
from tako.core.compiler import types
from tako.core.compiler.conversions import mir
from tako.util.qname import QName
from tako.util.cast import unwrap
from tako.util.graph import Graph
from tako.core.error import Error


def expand(conversions: Graph[QName, mir.RootConversion]) -> t.Optional[Error]:
    for src, target in list(conversions.links()):
        expanded = unwrap(conversions.get(src, target)).accept(RootExpander())
        if isinstance(expanded, Error):
            return expanded
        conversions.put(src, target, expanded)
    return None


class RootExpander(mir.RootConversionVisitor[t.Union[Error, mir.RootConversion]]):
    def visit_enum_conversion(
        self, conv: mir.EnumConversion
    ) -> t.Union[Error, mir.RootConversion]:
        needed = set(conv.src.variants.keys())
        new_mapping = []

        # Take everything that was explicitly mapped
        for m in conv.mapping:
            needed.remove(m.src.name)
            new_mapping.append(m)

        # For everything unmapped, try to map it to itself
        for unmapped in needed:
            if unmapped not in conv.target.variants:
                return Error(f"Variant {unmapped} not in target {conv.target}")
            else:
                new_mapping.append(
                    mir.EnumValueMapping(
                        mir.EnumValue(unmapped, conv.src.variants[unmapped]),
                        mir.EnumValue(unmapped, conv.target.variants[unmapped]),
                    )
                )

        return mir.EnumConversion(conv.protocol, conv.src, conv.target, new_mapping)

    def visit_struct_conversion(
        self, conv: mir.StructConversion
    ) -> t.Union[Error, mir.RootConversion]:
        needed = set(conv.target.fields.keys())
        new_mapping = {}

        # Take everything that was explicitly mapped
        for fname, m in conv.mapping.items():
            needed.remove(fname)
            new_mapping[fname] = m

        # For everything unmapped, try to keep the same field name in the
        # source and target
        for unmapped in needed:
            if unmapped not in conv.src.fields:
                return Error(f"Field {unmapped} not in source {conv.src}")
            else:
                new_mapping[unmapped] = mir.TransformFieldConversion(
                    unmapped,
                    mir.UnresolvedConversion(
                        conv.src.fields[unmapped].type_,
                        conv.target.fields[unmapped].type_,
                    ),
                )

        return mir.StructConversion(conv.protocol, conv.src, conv.target, new_mapping)

    def visit_variant_conversion(
        self, conv: mir.VariantConversion
    ) -> t.Union[Error, mir.RootConversion]:
        needed = set(conv.src.tags.keys())
        new_mapping = []

        # Take everything that was explicitly mapped
        for m in conv.mapping:
            needed.remove(m.src.type_)
            new_mapping.append(m)

        # For everything unmapped, try to map it to the same
        # type in the new variant
        # If the same type isn't in the target, put in an UnresolvedConversion
        # that keeps the tag the same, and we'll see if that works later.
        for unmapped in needed:
            if unmapped not in conv.target.tags:
                maybe_target_type = self.type_for_tag(
                    conv.src.tags[unmapped], conv.target
                )
                if maybe_target_type is None:
                    return Error(f"Variant {unmapped} not in target {conv.target}")
                else:
                    target_type = maybe_target_type
            else:
                target_type = unmapped

            new_mapping.append(
                mir.VariantValueMapping(
                    mir.VariantValue(unmapped, conv.src.tags[unmapped]),
                    mir.VariantValueConversion(
                        mir.VariantValue(target_type, conv.target.tags[target_type]),
                        mir.UnresolvedConversion(unmapped, target_type),
                    ),
                )
            )

        return mir.VariantConversion(conv.protocol, conv.src, conv.target, new_mapping)

    def type_for_tag(
        self, look_tag: int, variant: types.lir.Variant
    ) -> t.Optional[types.lir.Struct]:
        for type_, tag in variant.tags.items():
            if tag == look_tag:
                return type_
        return None
