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
from pathlib import Path
from tako.core.sir import tir
from tako.generators.cpp import cpp_gen as cg
from tako.util.int_model import Sign, Endianness, BITS_PER_BYTE
from tako.util.qname import QName
from tako.util.name_format import pascal_to_snake
from tako.runtime import ParseError
from tako.core.internal_error import InternalError

result_type = "::tako::Result"
make_unexpected = "::tl::make_unexpected"
optional_type = "::std::optional"
nullopt = "::std::nullopt"


def make_error_expr(expr: str) -> str:
    return f"{make_unexpected}({expr})"


def make_error(error: ParseError) -> str:
    return make_error_expr(f"::tako::ParseError::{error.name}")


def relative_path(qname: QName, subname: t.Optional[str] = None) -> Path:
    proto_name = pascal_to_snake(qname.name())
    proto_namespace = qname.namespace()
    base = Path(*proto_namespace.parts)
    if subname is not None:
        return base / proto_name / f"{subname}.hh"
    else:
        return base / f"{proto_name}.hh"


def wrap_in_namespace(namespace: QName, inner: cg.Node) -> cg.Node:
    for name in reversed(namespace.parts):
        inner = cg.Namespace(name, inner)
    return inner


def protocol_namespace(proto_qname: QName, extra: t.Optional[str] = None) -> QName:
    base = proto_qname.apply_to_name(pascal_to_snake)
    if extra is not None:
        return base.with_name(extra)
    else:
        return base


def cint_type(width: int, sign: Sign) -> str:
    prefix = sign_to_cpp_prefix(sign)
    return f"::std::{prefix}int{width * BITS_PER_BYTE}_t"


def cfloat_type(width: int) -> str:
    if width == 4:
        return "float"
    elif width == 8:
        return "double"
    else:
        raise InternalError(f"Bad width: {width}")


def cint_literal(width: int, sign: Sign, value: int) -> str:
    ctype = cint_type(width, sign)
    neg = "-" if value < 0 else ""
    return f"static_cast<{ctype}>({neg}UINT{width * BITS_PER_BYTE}_C({abs(value)}))"


def sign_to_cpp_prefix(sign: Sign) -> str:
    if sign == Sign.UNSIGNED:
        return "u"
    else:
        return ""


def endianness_to_cpp(e: Endianness) -> str:
    if e == Endianness.BIG:
        return "::tako::Endianness::BIG"
    else:
        return "::tako::Endianness::LITTLE"


def to_namespace(parts: t.Iterable[str]) -> str:
    return "::" + "::".join(parts)


def qname_to_cpp(qname: QName) -> str:
    return to_namespace(qname.parts)


@dataclasses.dataclass
class ViewCppType(tir.TypeVisitor[str]):
    @staticmethod
    def get_local_struct(type_: tir.Struct) -> str:
        return f"{type_.name.name()}View"

    @staticmethod
    def get_local_enum(type_: tir.Enum) -> str:
        return f"{type_.name.name()}"

    @staticmethod
    def get_local_variant(type_: tir.Variant) -> str:
        return f"{type_.name.name()}View"

    def visit_int(self, type_: tir.Int) -> str:
        return f"::tako::PrimitiveView<{cint_type(type_.width, type_.sign)}, {endianness_to_cpp(type_.endianness)}>"

    def visit_float(self, type_: tir.Float) -> str:
        return f"::tako::PrimitiveView<{cfloat_type(type_.width)}, {endianness_to_cpp(type_.endianness)}>"

    def visit_array(self, type_: tir.Array) -> str:
        return f"::tako::ArrayView<{type_.inner.accept(self)}, {type_.length}>"

    def visit_vector(self, type_: tir.Vector) -> str:
        return f"::tako::VectorView<{type_.inner.accept(self)}>"

    def visit_list(self, type_: tir.List) -> str:
        return f"::tako::ListView<{type_.inner.accept(self)}>"

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> str:
        return type_.variant.accept(self)

    def visit_virtual(self, type_: tir.Virtual) -> str:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> str:
        return self.namespace(root, ViewCppType.get_local_struct(root))

    def visit_variant(self, root: tir.Variant) -> str:
        return self.namespace(root, ViewCppType.get_local_variant(root))

    def visit_enum(self, root: tir.Enum) -> str:
        return self.namespace(root, ViewCppType.get_local_enum(root))

    def namespace(self, type_: tir.RootType, local_name: str) -> str:
        return qname_to_cpp(
            protocol_namespace(type_.name.namespace()).with_name(local_name)
        )


@dataclasses.dataclass
class OwnedCppType(tir.TypeVisitor[str]):
    @staticmethod
    def get_local_struct(type_: tir.Struct) -> str:
        return f"{type_.name.name()}"

    @staticmethod
    def get_local_enum(type_: tir.Enum) -> str:
        return f"{type_.name.name()}"

    @staticmethod
    def get_local_variant(type_: tir.Variant) -> str:
        return f"{type_.name.name()}"

    def visit_int(self, type_: tir.Int) -> str:
        return cint_type(type_.width, type_.sign)

    def visit_float(self, type_: tir.Float) -> str:
        return cfloat_type(type_.width)

    def visit_array(self, type_: tir.Array) -> str:
        return f"::std::array<{type_.inner.accept(self)}, {type_.length}>"

    def visit_vector(self, type_: tir.Vector) -> str:
        return f"::std::vector<{type_.inner.accept(self)}>"

    def visit_list(self, type_: tir.List) -> str:
        return f"::std::vector<{type_.inner.accept(self)}>"

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> str:
        return type_.variant.accept(self)

    def visit_virtual(self, type_: tir.Virtual) -> str:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> str:
        return self.namespace(root, OwnedCppType.get_local_struct(root))

    def visit_variant(self, root: tir.Variant) -> str:
        return self.namespace(root, OwnedCppType.get_local_variant(root))

    def visit_enum(self, root: tir.Enum) -> str:
        return self.namespace(root, OwnedCppType.get_local_enum(root))

    def namespace(self, type_: tir.RootType, local_name: str) -> str:
        return qname_to_cpp(
            protocol_namespace(type_.name.namespace()).with_name(local_name)
        )
