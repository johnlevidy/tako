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
import abc
import dataclasses
from tako.core.compiler import types
from tako.core.compiler.conversions import properties, mir
from tako.util.qname import QName
from tako.core.internal_error import QuirkAbstractDataclass
from tako.util.graph import Graph

T = t.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class ProtocolConversions:
    conversions: Graph[QName, RootConversion]
    own: t.List[RootConversion]


ConversionStrength = properties.ConversionStrength


@dataclasses.dataclass(frozen=True)
class Conversion:
    strength: ConversionStrength
    src: types.lir.Type
    target: types.lir.Type

    def accept(self, visitor: ConversionVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


@dataclasses.dataclass(frozen=True)
class RootConversion(Conversion):
    src: types.lir.RootType
    target: types.lir.RootType

    # protocol where conversion is defined
    protocol: QName

    def accept(self, visitor: ConversionVisitor[T]) -> T:
        return self.accept_r(visitor)

    def accept_r(self, visitor: RootConversionVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


class RootConversionVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_enum_conversion(self, conversion: EnumConversion) -> T:
        ...

    @abc.abstractmethod
    def visit_struct_conversion(self, conversion: StructConversion) -> T:
        ...

    @abc.abstractmethod
    def visit_variant_conversion(self, conversion: VariantConversion) -> T:
        ...


class ConversionVisitor(RootConversionVisitor[T], t.Generic[T]):
    @abc.abstractmethod
    def visit_identity_conversion(self, conversion: IdentityConversion) -> T:
        ...


@dataclasses.dataclass(frozen=True)
class EnumConversion(RootConversion):
    src: types.lir.Enum
    target: types.lir.Enum
    mapping: t.List[EnumValueMapping]

    def accept_r(self, visitor: RootConversionVisitor[T]) -> T:
        return visitor.visit_enum_conversion(self)


EnumValue = mir.EnumValue
EnumValueMapping = mir.EnumValueMapping


@dataclasses.dataclass(frozen=True)
class StructConversion(RootConversion):
    src: types.lir.Struct
    target: types.lir.Struct
    # From target field name to conversion which produces it
    mapping: t.Dict[str, FieldConversion]

    def accept_r(self, visitor: RootConversionVisitor[T]) -> T:
        return visitor.visit_struct_conversion(self)


@dataclasses.dataclass(frozen=True)
class FieldConversion:
    def accept(self, visitor: FieldConversionVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


class FieldConversionVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_int_default_field_conversion(
        self, conversion: IntDefaultFieldConversion
    ) -> T:
        ...

    @abc.abstractmethod
    def visit_enum_default_field_conversion(
        self, conversion: EnumDefaultFieldConversion
    ) -> T:
        ...

    @abc.abstractmethod
    def visit_transform_field_conversion(
        self, conversion: TransformFieldConversion
    ) -> T:
        ...


@dataclasses.dataclass(frozen=True)
class IntDefaultFieldConversion(FieldConversion):
    type_: types.lir.Int
    value: int

    def accept(self, visitor: FieldConversionVisitor[T]) -> T:
        return visitor.visit_int_default_field_conversion(self)


@dataclasses.dataclass(frozen=True)
class EnumDefaultFieldConversion(FieldConversion):
    type_: types.lir.Enum
    value: EnumValue

    def accept(self, visitor: FieldConversionVisitor[T]) -> T:
        return visitor.visit_enum_default_field_conversion(self)


@dataclasses.dataclass(frozen=True)
class TransformFieldConversion(FieldConversion):
    src_field: str
    conversion: Conversion

    def accept(self, visitor: FieldConversionVisitor[T]) -> T:
        return visitor.visit_transform_field_conversion(self)


@dataclasses.dataclass(frozen=True)
class VariantConversion(RootConversion):
    src: types.lir.Variant
    target: types.lir.Variant
    mapping: t.List[VariantValueMapping]

    def accept_r(self, visitor: RootConversionVisitor[T]) -> T:
        return visitor.visit_variant_conversion(self)


VariantValue = mir.VariantValue


@dataclasses.dataclass(frozen=True)
class VariantValueConversion:
    target: VariantValue
    conversion: Conversion


@dataclasses.dataclass(frozen=True)
class VariantValueMapping:
    src: VariantValue
    target: t.Optional[VariantValueConversion]


@dataclasses.dataclass(frozen=True)
class IdentityConversion(Conversion):
    def accept(self, visitor: ConversionVisitor[T]) -> T:
        return visitor.visit_identity_conversion(self)
