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

import dataclasses
from tako.core.compiler.conversions import mir, lir, properties
from tako.util.qname import QName
from tako.util.cast import unwrap, checked_cast
from tako.util.graph import Graph


def fuse(
    conversion_graph: Graph[QName, mir.RootConversion],
    properties: Graph[QName, properties.ConversionStrength],
) -> Graph[QName, lir.RootConversion]:
    result: Graph[QName, lir.RootConversion] = Graph()
    for src, target, conversion in conversion_graph:
        result.put(
            src,
            target,
            checked_cast(
                lir.RootConversion,
                conversion.accept(Fuse(conversion_graph, properties)),
            ),
        )
    return result


@dataclasses.dataclass
class Fuse(
    mir.ResolvingConversionVisitor[lir.Conversion],
    mir.FieldConversionVisitor[lir.FieldConversion],
):
    properties: Graph[QName, lir.ConversionStrength]

    def visit_enum_conversion(self, conversion: mir.EnumConversion) -> lir.Conversion:
        return lir.EnumConversion(
            strength=unwrap(
                self.properties.get(conversion.src.name, conversion.target.name)
            ),
            src=conversion.src,
            target=conversion.target,
            protocol=conversion.protocol,
            mapping=conversion.mapping,
        )

    def visit_struct_conversion(
        self, conversion: mir.StructConversion
    ) -> lir.Conversion:
        return lir.StructConversion(
            strength=unwrap(
                self.properties.get(conversion.src.name, conversion.target.name)
            ),
            src=conversion.src,
            target=conversion.target,
            protocol=conversion.protocol,
            mapping={
                fname: fc.accept(self) for fname, fc in conversion.mapping.items()
            },
        )

    def visit_variant_conversion(
        self, conversion: mir.VariantConversion
    ) -> lir.Conversion:
        return lir.VariantConversion(
            strength=unwrap(
                self.properties.get(conversion.src.name, conversion.target.name)
            ),
            src=conversion.src,
            target=conversion.target,
            protocol=conversion.protocol,
            mapping=[self.handle_vvm(m) for m in conversion.mapping],
        )

    def handle_vvm(self, vvm: mir.VariantValueMapping) -> lir.VariantValueMapping:
        if vvm.target is None:
            target = None
        else:
            target = lir.VariantValueConversion(
                vvm.target.target, vvm.target.conversion.accept(self)
            )
        return lir.VariantValueMapping(vvm.src, target)

    def visit_identity_conversion(
        self, conversion: mir.IdentityConversion
    ) -> lir.Conversion:
        return lir.IdentityConversion(
            strength=properties.compute_conversion_properties(conversion, self.convs),
            src=conversion.src,
            target=conversion.target,
        )

    def visit_int_default_field_conversion(
        self, conversion: mir.IntDefaultFieldConversion
    ) -> lir.FieldConversion:
        return lir.IntDefaultFieldConversion(conversion.type_, conversion.value)

    def visit_enum_default_field_conversion(
        self, conversion: mir.EnumDefaultFieldConversion
    ) -> lir.FieldConversion:
        return lir.EnumDefaultFieldConversion(conversion.type_, conversion.value)

    def visit_transform_field_conversion(
        self, conversion: mir.TransformFieldConversion
    ) -> lir.FieldConversion:
        return lir.TransformFieldConversion(
            conversion.src_field, conversion.conversion.accept(self)
        )
