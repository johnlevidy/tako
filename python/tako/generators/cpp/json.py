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
from tako.util.qname import QName
from tako.core.sir import Protocol, tir
from tako.generators.cpp import cpp_gen as cg
from tako.util.cast import assert_never
from tako.util.pretty_printer import PrettyPrinter
from tako.generators.template import template_raw
from tako.generators.cpp import core
from tako.generators.cpp.types import (
    relative_path,
    wrap_in_namespace,
    OwnedCppType,
    protocol_namespace,
    cint_literal,
    cint_type,
    cfloat_type,
    qname_to_cpp,
)


def generate(proto: Protocol, out_dir: Path) -> None:
    proto_file = out_dir / out_relative_path(proto.name)
    proto_file.parent.mkdir(parents=True, exist_ok=True)
    with proto_file.open("w") as out:
        cpp_node = generate_node(proto)
        printer = PrettyPrinter(4, out)
        cpp_node.pretty_printer(printer)


def out_relative_path(qname: QName) -> Path:
    return relative_path(qname, "json")


def generate_node(proto: Protocol) -> cg.Node:
    return cg.File(
        includes=[
            cg.Include("nlohmann/json.hpp"),
            cg.Include("tako/json.hh"),
            cg.Include(str(core.out_relative_path(proto.name))),
        ]
        + [
            cg.Include(str(out_relative_path(ext)))
            for ext in proto.types.external_protocols
        ],
        body=cg.Section(
            [
                cg.Raw(
                    '''\
                    #pragma GCC diagnostic push
                    #pragma GCC diagnostic ignored "-Wunused-parameter"'''
                ),
                wrap_in_namespace(
                    QName(("nlohmann",)),
                    cg.Section(
                        [
                            proto.types.types[root].accept_rtv(ToJsonGenerator())
                            for root in proto.types.own
                        ]
                    ),
                ),
                wrap_in_namespace(
                    protocol_namespace(proto.name, "json"),
                    cg.Section(
                        [
                            proto.types.types[root].accept_rtv(FromJsonGenerator())
                            for root in proto.types.own
                        ]
                    ),
                ),
                wrap_in_namespace(
                    protocol_namespace(proto.name),
                    cg.Section(
                        [
                            gen_public_functions(proto.types.types[root])
                            for root in proto.types.own
                            if isinstance(proto.types.types[root], tir.Struct)
                        ]
                    ),
                ),
                cg.Raw("#pragma GCC diagnostic pop"),
            ]
        ),
        pragma_once=True,
    )


@dataclasses.dataclass
class ToJsonGenerator(tir.RootTypeVisitor[cg.Node]):
    def visit_struct(self, root: tir.Struct) -> cg.Node:
        body: t.List[cg.Node] = []
        for fname, field in root.get_non_virtual():
            if field.master_field is not None:
                if field.master_field.key_property == tir.KeyProperty.VARIANT_TAG:
                    fvalue_expr = f"{field.master_field.master_field}.tag()"
                elif field.master_field.key_property == tir.KeyProperty.SEQ_LENGTH:
                    fvalue_expr = f"{field.master_field.master_field}.size()"
                else:
                    assert_never(field.master_field.key_property)
            else:
                fvalue_expr = f"{fname}"
            body.append(cg.Raw(f'j["{fname}"] = x.{fvalue_expr};'))

        return gen_adl_serializer(root, cg.Section(body))

    def visit_variant(self, root: tir.Variant) -> cg.Node:
        return gen_adl_serializer(
            root,
            cg.Raw(
                f"""\
            x.accept([&](auto&& v) {{
                j = v;
            }});"""
            ),
        )

    def visit_enum(self, root: tir.Enum) -> cg.Node:
        return gen_adl_serializer(root, cg.Raw(f"j = x.value();"))


def gen_adl_serializer(root: tir.Type, inner: cg.Node) -> cg.Node:
    return cg.Class(
        f"adl_serializer<{root.accept(OwnedCppType())}>",
        [],
        [
            (
                cg.Visibility.PUBLIC,
                cg.Section(
                    [
                        cg.Function(
                            "to_json",
                            [
                                (cg.Type("::nlohmann::json&"), "j"),
                                (cg.Type(root.accept(OwnedCppType())), "x"),
                            ],
                            cg.Type("void"),
                            inner,
                            static=True,
                        )
                    ]
                ),
            )
        ],
        template_args="",
        is_struct=True,
    )


@dataclasses.dataclass
class FromJsonGenerator(tir.RootTypeVisitor[cg.Node]):
    def visit_struct(self, root: tir.Struct) -> cg.Node:
        owned_class_name = root.accept(OwnedCppType())
        class_name = JsonType.get_local_struct(root)

        def resolve_arg(x: t.Union[int, str]) -> str:
            if isinstance(x, int):
                return str(x)
            elif isinstance(x, str):
                return f"*{x}"
            else:
                assert_never(x)

        parts = [
            (
                fname,
                field.type_.accept(JsonType()),
                ", ".join(
                    [f'j["{fname}"]']
                    + core.resolve_field_args(resolve_arg, field.type_)
                ),
            )
            for fname, field in root.get_non_virtual()
        ]

        return gen_raw(
            """
            class {{ class_name }} {
            public:
                using Built = {{ owned_class_name }};
                static ::tako::Result<{{ owned_class_name }}> from_json(const ::nlohmann::json& j) {
                    {%- for fname, json_type, args in parts %}
                    auto {{ fname }} = {{ json_type }}::from_json({{ args }});
                    if (!{{ fname }}) {
                        return ::tl::make_unexpected({{ fname }}.error());
                    }
                    {%- endfor %}
                    return {{ owned_class_name }} {
                        {%- for fname, _ in root.get_owned() %}
                        .{{ fname}} = ::std::move(*{{ fname }}){{ "," if not loop.last }}
                        {%- endfor %}
                    };
                }
                static ::nlohmann::json to_json(const {{ owned_class_name }}& x) {
                    return x;
                }
            };
        """,
            locals(),
        )

    def visit_variant(self, root: tir.Variant) -> cg.Node:
        owned_class_name = root.accept(OwnedCppType())
        class_name = JsonType.get_local_variant(root)
        tag_ctype = root.tag_type.accept(OwnedCppType())
        variants = [
            (
                variant_type.accept(JsonType()),
                cint_literal(root.tag_type.width, root.tag_type.sign, tag_value),
            )
            for variant_type, tag_value in root.tags.items()
        ]
        return gen_raw(
            """
            class {{ class_name }} {
            public:
                using Built = {{ owned_class_name }};
                static ::tako::Result<{{ owned_class_name }}> from_json(const ::nlohmann::json& j, {{ tag_ctype }} tag) {
                    {%- for variant_type, tag_value in variants %}
                    if (tag == {{ tag_value }}) {
                        auto maybe = {{ variant_type }}::from_json(j);
                        if (!maybe) {
                            return tl::make_unexpected(maybe.error());
                        } else {
                            return {{ owned_class_name }}{*maybe};
                        }
                    }
                    {%- endfor %}
                    return ::tl::make_unexpected(::tako::ParseError::MALFORMED);
                }
                static ::nlohmann::json to_json(const {{ owned_class_name }}& x) {
                    return x;
                }
            };
        """,
            locals(),
        )

    def visit_enum(self, root: tir.Enum) -> cg.Node:
        owned_class_name = root.accept(OwnedCppType())
        class_name = JsonType.get_local_enum(root)
        underlying = root.underlying_type.accept(JsonType())
        return gen_raw(
            """
            class {{ class_name }} {
            public:
                using Built = {{ owned_class_name }};
                static ::tako::Result<{{ owned_class_name }}> from_json(const ::nlohmann::json& j) {
                    auto val = {{ underlying }}::from_json(j);
                    if (!val) {
                        return ::tl::make_unexpected(val.error());
                    } else {
                        auto res = {{ owned_class_name }}::make_unsafe(*val);
                        if (res.valid()) {
                            return res;
                        } else {
                            return ::tl::make_unexpected(::tako::ParseError::MALFORMED);
                        }
                    }
                }
            };
        """,
            locals(),
        )


def gen_public_functions(root: tir.Type) -> cg.Node:
    return cg.Raw(
        f"""\
        inline ::nlohmann::json serialize_json(const {root.accept(OwnedCppType())}& x) {{
            return x;
        }}
        inline ::tako::Result<{root.accept(OwnedCppType())}> parse_json(const ::nlohmann::json& j, ::tako::Type<{root.accept(OwnedCppType())}>) {{
            return {root.accept(JsonType())}::from_json(j);
        }}"""
    )


@dataclasses.dataclass
class JsonType(tir.TypeVisitor[str]):
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
        return f"::tako::PrimitiveJson<{cint_type(type_.width, type_.sign)}>"

    def visit_float(self, type_: tir.Float) -> str:
        return f"::tako::PrimitiveJson<{cfloat_type(type_.width)}>"

    def visit_array(self, type_: tir.Array) -> str:
        return f"::tako::ArrayJson<{type_.inner.accept(self)}, {type_.length}>"

    def visit_vector(self, type_: tir.Vector) -> str:
        return f"::tako::VectorJson<{type_.inner.accept(self)}>"

    def visit_list(self, type_: tir.List) -> str:
        return f"::tako::VectorJson<{type_.inner.accept(self)}>"

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> str:
        return type_.variant.accept(self)

    def visit_virtual(self, type_: tir.Virtual) -> str:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> str:
        return self.namespace(root, JsonType.get_local_struct(root))

    def visit_variant(self, root: tir.Variant) -> str:
        return self.namespace(root, JsonType.get_local_variant(root))

    def visit_enum(self, root: tir.Enum) -> str:
        return self.namespace(root, JsonType.get_local_enum(root))

    def namespace(self, type_: tir.RootType, local_name: str) -> str:
        return qname_to_cpp(
            protocol_namespace(type_.name.namespace(), "json").with_name(local_name)
        )


def gen_raw(template: str, env: t.Dict[str, t.Any]) -> cg.Raw:
    return cg.Raw(template_raw(template, {**globals(), **env}))
