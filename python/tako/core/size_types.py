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

T = t.TypeVar("T")


class Size(abc.ABC):
    @abc.abstractmethod
    def accept(self, visitor: SizeVisitor[T]) -> T:
        ...


class SizeVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_constant(self, size: Constant) -> T:
        ...

    @abc.abstractmethod
    def visit_dynamic(self, size: Dynamic) -> T:
        ...


@dataclasses.dataclass(frozen=True)
class Constant(Size):
    # in bytes
    value: int

    def accept(self, visitor: SizeVisitor[T]) -> T:
        return visitor.visit_constant(self)


@dataclasses.dataclass(frozen=True)
class Dynamic(Size):
    def accept(self, visitor: SizeVisitor[T]) -> T:
        return visitor.visit_dynamic(self)


@dataclasses.dataclass(frozen=True)
class Offset:
    # Represents an offset of offset bytes, where byte 0 is
    # the byte immediately after the base field, if any.
    # If base is None, then offset starts from the start of the current
    # struct.
    base: t.Optional[str]
    offset: int

    @staticmethod
    def zero() -> Offset:
        return Offset(None, 0)

    def add(self, name: str, size: Size) -> Offset:
        return size.accept(Adder(self, name))

    def as_size(self) -> Size:
        if self.base is None:
            return Constant(self.offset)
        else:
            return Dynamic()


@dataclasses.dataclass
class Adder(SizeVisitor[Offset]):
    target: Offset
    field_name: str

    def visit_constant(self, size: Constant) -> Offset:
        return Offset(self.target.base, self.target.offset + size.value)

    def visit_dynamic(self, size: Dynamic) -> Offset:
        return Offset(self.field_name, 0)


@dataclasses.dataclass(frozen=True)
class SizeSum:
    # Represents a size that is the sum of the base, plus a list of named fields
    base: int
    names: t.List[str]

    @staticmethod
    def zero() -> SizeSum:
        return SizeSum(0, [])

    def add(self, name: str, size: Size) -> SizeSum:
        return size.accept(SumAdder(self, name))


@dataclasses.dataclass
class SumAdder(SizeVisitor[SizeSum]):
    target: SizeSum
    field_name: str

    def visit_constant(self, size: Constant) -> SizeSum:
        return SizeSum(self.target.base + size.value, self.target.names)

    def visit_dynamic(self, size: Dynamic) -> SizeSum:
        return SizeSum(self.target.base, self.target.names + [self.field_name])
