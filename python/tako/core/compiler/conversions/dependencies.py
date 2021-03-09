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
from tako.core.compiler.conversions import mir
from tako.util.qname import QName
from tako.core.internal_error import InternalError
from tako.util.graph import Graph


@dataclasses.dataclass(frozen=True)
class ConversionHandle:
    src: QName
    target: QName

    def __str__(self) -> str:
        return f"{self.src} -> {self.target}"


def build_dependency_graph(
    convs: Graph[QName, mir.RootConversion]
) -> Graph[ConversionHandle, None]:
    result: Graph[ConversionHandle, None] = Graph()
    for rc in convs.edges():
        rc_handle = ConversionHandle(rc.src.name, rc.target.name)
        for dependency in rc.accept(FindDependencies()):
            if isinstance(dependency, mir.ConversionRef):
                result.put(
                    rc_handle,
                    ConversionHandle(dependency.src.name, dependency.target.name),
                    None,
                )

    return result


@dataclasses.dataclass
class FindDependencies(
    mir.RootConversionVisitor[t.Iterator[mir.Conversion]],
    mir.ConversionVisitor[t.Iterator[mir.Conversion]],
    mir.FieldConversionVisitor[t.Iterator[mir.Conversion]],
):
    def visit_enum_conversion(
        self, conv: mir.EnumConversion
    ) -> t.Iterator[mir.Conversion]:
        return iter(())

    def visit_struct_conversion(
        self, conv: mir.StructConversion
    ) -> t.Iterator[mir.Conversion]:
        for sfc in conv.mapping.values():
            for dep_conv in sfc.accept(self):
                yield dep_conv

    def visit_variant_conversion(
        self, conv: mir.VariantConversion
    ) -> t.Iterator[mir.Conversion]:
        for vvc in conv.mapping:
            if vvc.target is not None:
                yield vvc.target.conversion

    def visit_identity_conversion(
        self, conv: mir.IdentityConversion
    ) -> t.Iterator[mir.Conversion]:
        return iter(())

    def visit_unresolved_conversion(
        self, conv: mir.UnresolvedConversion
    ) -> t.Iterator[mir.Conversion]:
        raise InternalError()

    def visit_conversion_ref(
        self, conv: mir.ConversionRef
    ) -> t.Iterator[mir.Conversion]:
        yield conv

    def visit_int_default_field_conversion(
        self, conv: mir.IntDefaultFieldConversion
    ) -> t.Iterator[mir.Conversion]:
        return iter(())

    def visit_enum_default_field_conversion(
        self, conv: mir.EnumDefaultFieldConversion
    ) -> t.Iterator[mir.Conversion]:
        return iter(())

    def visit_transform_field_conversion(
        self, conv: mir.TransformFieldConversion
    ) -> t.Iterator[mir.Conversion]:
        yield conv.conversion
