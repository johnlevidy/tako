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

import dataclasses
from dataclasses import replace
from tako.util.qname import QName
from tako.util.graph import Graph
from tako.core.sir import Protocol, tir, kir, cir
from tako.util.cast import checked_cast


def prefix(proto: Protocol, namespace: QName) -> Protocol:
    if len(namespace) == 0:
        return proto

    return Protocol(
        name=proto.name.prefix(namespace),
        types=tir.ProtocolTypes(
            types={
                name.prefix(namespace): checked_cast(
                    tir.RootType, type_.accept(TypePrefix(namespace))
                )
                for name, type_ in proto.types.types.items()
            },
            own=[name.prefix(namespace) for name in proto.types.own],
            external_protocols={
                name.prefix(namespace) for name in proto.types.external_protocols
            },
        ),
        constants=kir.ProtocolConstants(
            constants={
                name.prefix(namespace): constant.accept(ConstantPrefix(namespace))
                for name, constant in proto.constants.constants.items()
            }
        ),
        conversions=cir.ProtocolConversions(
            conversions=Graph.from_iterable(
                [
                    (
                        src_name.prefix(namespace),
                        target_name.prefix(namespace),
                        checked_cast(
                            cir.RootConversion,
                            conv.accept_r(ConversionPrefix(namespace)),
                        ),
                    )
                    for src_name, target_name, conv in proto.conversions.conversions
                ]
            ),
            own=[
                checked_cast(
                    cir.RootConversion, conv.accept_r(ConversionPrefix(namespace))
                )
                for conv in proto.conversions.own
            ],
        ),
    )


@dataclasses.dataclass
class TypePrefix(tir.TypeVisitor[tir.Type]):
    namespace: QName

    def visit_struct(self, root: tir.Struct) -> tir.Struct:
        return replace(
            root,
            name=root.name.prefix(self.namespace),
            fields={
                name: replace(
                    field,
                    type_=field.type_.accept(self),
                    master_field=replace(
                        field.master_field, type_=field.master_field.type_.accept(self)
                    )
                    if field.master_field is not None
                    else None,
                )
                for name, field in root.fields.items()
            },
        )

    def visit_variant(self, root: tir.Variant) -> tir.Type:
        return replace(
            root,
            name=root.name.prefix(self.namespace),
            tag_type=root.tag_type.accept(self),
            tags={
                checked_cast(tir.Struct, struct.accept(self)): value
                for struct, value in root.tags.items()
            },
        )

    def visit_enum(self, root: tir.Enum) -> tir.Type:
        return replace(
            root,
            name=root.name.prefix(self.namespace),
            underlying_type=root.underlying_type.accept(self),
        )

    def visit_int(self, type_: tir.Int) -> tir.Type:
        return type_

    def visit_float(self, type_: tir.Float) -> tir.Type:
        return type_

    def visit_array(self, type_: tir.Array) -> tir.Type:
        return replace(type_, inner=type_.inner.accept(self))

    def visit_vector(self, type_: tir.Vector) -> tir.Type:
        return replace(type_, inner=type_.inner.accept(self))

    def visit_list(self, type_: tir.List) -> tir.Type:
        return replace(type_, inner=type_.inner.accept(self))

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> tir.Type:
        return replace(type_, variant=type_.variant.accept(self))

    def visit_virtual(self, type_: tir.Virtual) -> tir.Type:
        return replace(type_, inner=type_.inner.accept(self))


@dataclasses.dataclass
class ConstantPrefix(kir.RootConstantVisitor[kir.RootConstant]):
    namespace: QName

    def visit_int_constant(self, constant: kir.RootIntConstant) -> kir.RootConstant:
        return replace(
            constant,
            name=constant.name.prefix(self.namespace),
            type_=constant.type_.accept(TypePrefix(self.namespace)),
        )

    def visit_string_constant(
        self, constant: kir.RootStringConstant
    ) -> kir.RootConstant:
        return replace(constant, name=constant.name.prefix(self.namespace))


@dataclasses.dataclass
class ConversionPrefix(
    cir.ConversionVisitor[cir.Conversion],
    cir.FieldConversionVisitor[cir.FieldConversion],
):
    namespace: QName

    def visit_enum_conversion(self, conversion: cir.EnumConversion) -> cir.Conversion:
        return replace(
            conversion,
            src=checked_cast(
                tir.Enum, conversion.src.accept(TypePrefix(self.namespace))
            ),
            target=checked_cast(
                tir.Enum, conversion.target.accept(TypePrefix(self.namespace))
            ),
            protocol=conversion.protocol.prefix(self.namespace),
        )

    def visit_struct_conversion(
        self, conversion: cir.StructConversion
    ) -> cir.Conversion:
        return replace(
            conversion,
            src=checked_cast(
                tir.Struct, conversion.src.accept(TypePrefix(self.namespace))
            ),
            target=checked_cast(
                tir.Struct, conversion.target.accept(TypePrefix(self.namespace))
            ),
            protocol=conversion.protocol.prefix(self.namespace),
            mapping={
                fname: fc.accept(self) for fname, fc in conversion.mapping.items()
            },
        )

    def visit_int_default_field_conversion(
        self, conversion: cir.IntDefaultFieldConversion
    ) -> cir.FieldConversion:
        return replace(
            conversion, type_=conversion.type_.accept(TypePrefix(self.namespace))
        )

    def visit_enum_default_field_conversion(
        self, conversion: cir.EnumDefaultFieldConversion
    ) -> cir.FieldConversion:
        return replace(
            conversion, type_=conversion.type_.accept(TypePrefix(self.namespace))
        )

    def visit_transform_field_conversion(
        self, conversion: cir.TransformFieldConversion
    ) -> cir.FieldConversion:
        return replace(conversion, conversion=conversion.conversion.accept(self))

    def visit_variant_conversion(
        self, conversion: cir.VariantConversion
    ) -> cir.Conversion:
        return replace(
            conversion,
            src=checked_cast(
                tir.Variant, conversion.src.accept(TypePrefix(self.namespace))
            ),
            target=checked_cast(
                tir.Variant, conversion.target.accept(TypePrefix(self.namespace))
            ),
            protocol=conversion.protocol.prefix(self.namespace),
            mapping=[
                cir.VariantValueMapping(
                    src=replace(
                        vvm.src, type_=vvm.src.type_.accept(TypePrefix(self.namespace))
                    ),
                    target=cir.VariantValueConversion(
                        target=replace(
                            vvm.target.target,
                            type_=vvm.target.target.type_.accept(
                                TypePrefix(self.namespace)
                            ),
                        ),
                        conversion=vvm.target.conversion.accept(self),
                    )
                    if vvm.target is not None
                    else None,
                )
                for vvm in conversion.mapping
            ],
        )

    def visit_identity_conversion(
        self, conversion: cir.IdentityConversion
    ) -> cir.Conversion:
        return replace(
            conversion,
            src=conversion.src.accept(TypePrefix(self.namespace)),
            target=conversion.target.accept(TypePrefix(self.namespace)),
        )
