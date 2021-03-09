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
import tako.core.size_types as st
from tako.util.ranges import Range
from tako.core.compiler.types import mir
from tako.util.int_model import Sign, Endianness
from tako.util.qname import QName
from tako.core.compiler.types import master_fields
from tako.core.compiler.types.hash_expand import Digest
from tako.core.internal_error import QuirkAbstractDataclass

T = t.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class ProtocolTypes:
    types: t.Dict[QName, RootType]
    # Ordered in topological order with leaves first
    own: t.List[QName]
    external_protocols: t.Set[QName]


@dataclasses.dataclass(frozen=True)
class Type:
    size: st.Size = dataclasses.field(compare=False)
    trivial: bool

    def accept(self, visitor: TypeVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


@dataclasses.dataclass(frozen=True)
class RootType(Type):
    name: QName
    digest: Digest

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return self.accept_rtv(visitor)

    def accept_rtv(self, visitor: RootTypeVisitor[T]) -> T:
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


class TypeVisitor(RootTypeVisitor[T], t.Generic[T]):
    @abc.abstractmethod
    def visit_int(self, type_: Int) -> T:
        ...

    @abc.abstractmethod
    def visit_float(self, type_: Float) -> T:
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


@dataclasses.dataclass(frozen=True)
class Struct(RootType):
    fields: t.Dict[str, Field] = dataclasses.field(compare=False)
    tail_offset: st.Offset = dataclasses.field(compare=False)

    def accept_rtv(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_struct(self)

    def get_non_virtual(self) -> t.Generator[t.Tuple[str, Field], None, None]:
        for fname, field in self.fields.items():
            if not isinstance(field.type_, Virtual):
                yield fname, field

    def get_non_virtual_dynamic(self) -> t.Generator[t.Tuple[str, Field], None, None]:
        for fname, field in self.get_non_virtual():
            if isinstance(field.type_.size, st.Dynamic):
                yield fname, field

    def get_owned(self) -> t.Generator[t.Tuple[str, Field], None, None]:
        for fname, field in self.get_non_virtual():
            if field.master_field is None:
                yield fname, field


@dataclasses.dataclass(frozen=True)
class Field:
    type_: Type
    offset: st.Offset
    master_field: t.Optional[MasterField]


@dataclasses.dataclass(frozen=True)
class MasterField:
    master_field: str
    type_: Type
    key_property: KeyProperty


KeyProperty = master_fields.KeyProperty


@dataclasses.dataclass(frozen=True)
class Variant(RootType):
    tag_type: Int
    tags: t.Dict[Struct, int] = dataclasses.field(compare=False)

    def accept_rtv(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_variant(self)


@dataclasses.dataclass(frozen=True)
class Enum(RootType):
    underlying_type: Int = dataclasses.field(compare=False)
    variants: t.Dict[str, int] = dataclasses.field(compare=False)
    valid_ranges: t.List[Range] = dataclasses.field(compare=False)

    def accept_rtv(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_enum(self)


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


@dataclasses.dataclass(frozen=True)
class DetachedVariant(Type):
    variant: Variant
    tag: FieldReference

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_detached_variant(self)


@dataclasses.dataclass(frozen=True)
class Virtual(Type):
    inner: Type

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_virtual(self)


FieldReference = mir.FieldReference
Length = mir.Length
FixedLength = mir.FixedLength
VariableLength = mir.VariableLength
LengthVisitor = mir.LengthVisitor
