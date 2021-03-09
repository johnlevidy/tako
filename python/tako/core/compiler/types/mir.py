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

# Struct Intermediate Representation (SIR)
from __future__ import annotations

import typing as t
import dataclasses
import abc
from tako.util.int_model import Sign, Endianness
from tako.util.qname import QName
from tako.util.cast import checked_cast
from tako.core.internal_error import InternalError, QuirkAbstractDataclass

T = t.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class RootType:
    name: QName

    def accept(self, visitor: RootTypeVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


class RootTypeVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_struct(self, root: Struct) -> T:
        ...

    @abc.abstractmethod
    def visit_variant(self, root: Variant) -> T:
        ...

    @abc.abstractmethod
    def visit_enum(self, root: Enum) -> T:
        ...


@dataclasses.dataclass(frozen=True)
class Struct(RootType):
    fields: t.Dict[str, Type]

    def accept(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_struct(self)


@dataclasses.dataclass(frozen=True)
class Variant(RootType):
    tag_type: Int

    def types(self) -> t.Iterable[StructRef]:
        raise QuirkAbstractDataclass()

    def accept(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_variant(self)

    def accept_v(self, visitor: VariantVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


class VariantVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_fixed_variant(self, variant: FixedVariant) -> T:
        ...

    @abc.abstractmethod
    def visit_hash_variant(self, variant: HashVariant) -> T:
        ...


@dataclasses.dataclass(frozen=True)
class FixedVariant(Variant):
    tags: t.Dict[StructRef, int]

    def types(self) -> t.Iterable[StructRef]:
        return self.tags.keys()

    def accept_v(self, visitor: VariantVisitor[T]) -> T:
        return visitor.visit_fixed_variant(self)


@dataclasses.dataclass(frozen=True)
class HashVariant(Variant):
    hash_types: t.Set[StructRef]

    def types(self) -> t.Iterable[StructRef]:
        return self.hash_types

    def accept_v(self, visitor: VariantVisitor[T]) -> T:
        return visitor.visit_hash_variant(self)


@dataclasses.dataclass(frozen=True)
class Enum(RootType):
    underlying_type: Int
    variants: t.Dict[str, int]

    def accept(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_enum(self)


@dataclasses.dataclass(frozen=True)
class Type:
    def accept(self, visitor: TypeVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


class TypeVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_int(self, type_: Int) -> T:
        ...

    @abc.abstractmethod
    def visit_float(self, type_: Float) -> T:
        ...

    @abc.abstractmethod
    def visit_seq(self, type_: Seq) -> T:
        ...

    @abc.abstractmethod
    def visit_unbound_seq(self, type_: UnboundSeq) -> T:
        ...

    @abc.abstractmethod
    def visit_array(self, type_: Array) -> T:
        ...

    @abc.abstractmethod
    def visit_vector(self, type_: Vector) -> T:
        ...

    @abc.abstractmethod
    def visit_list(self, type_: List) -> T:
        ...

    @abc.abstractmethod
    def visit_detached_variant(self, type_: DetachedVariant) -> T:
        ...

    @abc.abstractmethod
    def visit_virtual(self, type_: Virtual) -> T:
        ...

    @abc.abstractmethod
    def visit_ref(self, type_: Ref) -> T:
        ...


class SeqTypeVisitor(TypeVisitor[T], t.Generic[T]):
    def visit_array(self, type_: Array) -> T:
        raise InternalError("Arrays should not be present")

    def visit_vector(self, type_: Vector) -> T:
        raise InternalError("Vectors should not be present")

    def visit_list(self, type_: List) -> T:
        raise InternalError("Lists should not be present")


class LoweredTypeVisitor(TypeVisitor[T], t.Generic[T]):
    def visit_seq(self, type_: Seq) -> T:
        raise InternalError("Seq is not a lowered type")

    def visit_unbound_seq(self, type_: UnboundSeq) -> T:
        raise InternalError("Seq is not a lowered type")


@dataclasses.dataclass(frozen=True)
class Int(Type):
    # in bytes
    width: int
    sign: Sign
    endianness: Endianness

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_int(self)


@dataclasses.dataclass(frozen=True)
class Float(Type):
    # in bytes
    width: int
    endianness: Endianness

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_float(self)


@dataclasses.dataclass(frozen=True)
class Seq(Type):
    inner: Type
    length: Length

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_seq(self)


@dataclasses.dataclass(frozen=True)
class UnboundSeq(Type):
    inner: Type
    length_type: Int

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_unbound_seq(self)


@dataclasses.dataclass(frozen=True)
class Array(Type):
    inner: Type
    length: int

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_array(self)


@dataclasses.dataclass(frozen=True)
class Vector(Type):
    inner: Type
    length: FieldReference

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_vector(self)


@dataclasses.dataclass(frozen=True)
class List(Type):
    inner: Type
    length: Length

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_list(self)


class Length(abc.ABC):
    @abc.abstractmethod
    def accept(self, visitor: LengthVisitor[T]) -> T:
        ...


class LengthVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_fixed_length(self, length: FixedLength) -> T:
        ...

    @abc.abstractmethod
    def visit_variable_length(self, length: VariableLength) -> T:
        ...


@dataclasses.dataclass(frozen=True)
class FixedLength(Length):
    length: int

    def accept(self, visitor: LengthVisitor[T]) -> T:
        return visitor.visit_fixed_length(self)


@dataclasses.dataclass(frozen=True)
class VariableLength(Length):
    length: FieldReference

    def accept(self, visitor: LengthVisitor[T]) -> T:
        return visitor.visit_variable_length(self)


@dataclasses.dataclass(frozen=True)
class DetachedVariant(Type):
    variant: VariantRef
    tag: FieldReference

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_detached_variant(self)


@dataclasses.dataclass(frozen=True)
class Virtual(Type):
    inner: Type

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_virtual(self)


@dataclasses.dataclass(frozen=True)
class Ref(Type):
    name: QName

    def resolve(self, context: t.Dict[QName, RootType]) -> RootType:
        raise QuirkAbstractDataclass()

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_ref(self)

    def accept_r(self, visitor: RefVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


class RefVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_struct_ref(self, ref: StructRef) -> T:
        ...

    @abc.abstractmethod
    def visit_variant_ref(self, ref: VariantRef) -> T:
        ...

    @abc.abstractmethod
    def visit_enum_ref(self, ref: EnumRef) -> T:
        ...


@dataclasses.dataclass(frozen=True)
class StructRef(Ref):
    def resolve(self, context: t.Dict[QName, RootType]) -> Struct:
        return checked_cast(Struct, context[self.name])

    def accept_r(self, visitor: RefVisitor[T]) -> T:
        return visitor.visit_struct_ref(self)


@dataclasses.dataclass(frozen=True)
class VariantRef(Ref):
    def resolve(self, context: t.Dict[QName, RootType]) -> Variant:
        return checked_cast(Variant, context[self.name])

    def accept_r(self, visitor: RefVisitor[T]) -> T:
        return visitor.visit_variant_ref(self)


@dataclasses.dataclass(frozen=True)
class EnumRef(Ref):
    def resolve(self, context: t.Dict[QName, RootType]) -> Enum:
        return checked_cast(Enum, context[self.name])

    def accept_r(self, visitor: RefVisitor[T]) -> T:
        return visitor.visit_enum_ref(self)


@dataclasses.dataclass(frozen=True)
class FieldReference:
    name: str
