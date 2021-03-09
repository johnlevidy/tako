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
from tako.util.qname import QName
from tako.core.internal_error import QuirkAbstractDataclass
from tako.core.compiler.types import lir

T = t.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class ProtocolConstants:
    constants: t.Dict[QName, RootConstant]


@dataclasses.dataclass(frozen=True)
class RootConstant:
    name: QName

    def accept(self, visitor: RootConstantVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


class RootConstantVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_int_constant(self, root: RootIntConstant) -> T:
        ...

    @abc.abstractmethod
    def visit_string_constant(self, root: RootStringConstant) -> T:
        ...


@dataclasses.dataclass(frozen=True)
class RootStringConstant(RootConstant):
    value: str

    def accept(self, visitor: RootConstantVisitor[T]) -> T:
        return visitor.visit_string_constant(self)


@dataclasses.dataclass(frozen=True)
class RootIntConstant(RootConstant):
    type_: lir.Int
    value: int

    def accept(self, visitor: RootConstantVisitor[T]) -> T:
        return visitor.visit_int_constant(self)
