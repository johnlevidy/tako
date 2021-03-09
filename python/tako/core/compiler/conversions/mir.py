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
from tako.core.compiler.types import lir
from tako.util.qname import QName
from tako.core.internal_error import QuirkAbstractDataclass, InternalError
from tako.util.graph import Graph
from tako.util.cast import unwrap

T = t.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class RootConversion:
    # protocol where conversion is defined
    protocol: QName
    src: lir.RootType
    target: lir.RootType

    def accept(self, visitor: RootConversionVisitor[T]) -> T:
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


@dataclasses.dataclass(frozen=True)
class Conversion:
    src: lir.Type
    target: lir.Type

    def accept(self, visitor: ConversionVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


class ConversionVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_identity_conversion(self, conversion: IdentityConversion) -> T:
        ...

    @abc.abstractmethod
    def visit_unresolved_conversion(self, conversion: UnresolvedConversion) -> T:
        ...

    @abc.abstractmethod
    def visit_conversion_ref(self, conversion: ConversionRef) -> T:
        ...


@dataclasses.dataclass(frozen=True)
class EnumConversion(RootConversion):
    src: lir.Enum
    target: lir.Enum
    mapping: t.List[EnumValueMapping]

    def accept(self, visitor: RootConversionVisitor[T]) -> T:
        return visitor.visit_enum_conversion(self)


@dataclasses.dataclass(frozen=True)
class EnumValue:
    name: str
    value: int


@dataclasses.dataclass(frozen=True)
class EnumValueMapping:
    src: EnumValue
    target: t.Optional[EnumValue]


@dataclasses.dataclass(frozen=True)
class StructConversion(RootConversion):
    src: lir.Struct
    target: lir.Struct
    # From target field name to conversion which produces it
    mapping: t.Dict[str, FieldConversion]

    def accept(self, visitor: RootConversionVisitor[T]) -> T:
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
    type_: lir.Int
    value: int

    def accept(self, visitor: FieldConversionVisitor[T]) -> T:
        return visitor.visit_int_default_field_conversion(self)


@dataclasses.dataclass(frozen=True)
class EnumDefaultFieldConversion(FieldConversion):
    type_: lir.Enum
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
    src: lir.Variant
    target: lir.Variant
    mapping: t.List[VariantValueMapping]

    def accept(self, visitor: RootConversionVisitor[T]) -> T:
        return visitor.visit_variant_conversion(self)


@dataclasses.dataclass(frozen=True)
class VariantValue:
    type_: lir.Struct
    value: int


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


@dataclasses.dataclass(frozen=True)
class UnresolvedConversion(Conversion):
    def accept(self, visitor: ConversionVisitor[T]) -> T:
        return visitor.visit_unresolved_conversion(self)


@dataclasses.dataclass(frozen=True)
class ConversionRef(Conversion):
    src: lir.RootType
    target: lir.RootType

    def resolve(self, graph: Graph[QName, RootConversion]) -> RootConversion:
        return unwrap(graph.get(self.src.name, self.target.name))

    def accept(self, visitor: ConversionVisitor[T]) -> T:
        return visitor.visit_conversion_ref(self)


@dataclasses.dataclass
class ResolvingConversionVisitor(  # type: ignore
    RootConversionVisitor[T], ConversionVisitor[T], t.Generic[T]
):
    convs: Graph[QName, RootConversion]

    def visit_conversion_ref(self, conv: ConversionRef) -> T:
        return conv.resolve(self.convs).accept(self)

    def visit_unresolved_conversion(self, conv: UnresolvedConversion) -> T:
        raise InternalError()
