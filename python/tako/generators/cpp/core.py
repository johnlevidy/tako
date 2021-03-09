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
import json
from pathlib import Path
from tako.core.sir import Protocol, tir, kir, cir
import tako.core.size_types as st
from tako.util.ranges import Range
from tako.generators.cpp import cpp_gen as cg
from tako.generators.cpp.class_builder import ClassBuilder, ClassParts
from tako.util.cast import assert_never
from tako.runtime import ParseError
from tako.util.pretty_printer import PrettyPrinter
from tako.generators.template import template_raw
from tako.util.int_model import Sign, representable_range
from tako.util.qname import QName
from tako.core.internal_error import InternalError
from tako.generators.cpp.types import (  # noqa
    optional_type,
    nullopt,
    make_error,
    relative_path,
    wrap_in_namespace,
    protocol_namespace,
    ViewCppType,
    OwnedCppType,
    cint_type,
    cint_literal,
    endianness_to_cpp,
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
    return relative_path(qname, "core")


def generate_node(proto: Protocol) -> cg.Node:
    sections: t.List[cg.Node] = []
    sections += [
        constant.accept(RootConstantGenerator())
        for constant in proto.constants.constants.values()
    ]
    sections += [
        proto.types.types[root].accept_rtv(RootTypeGenerator())
        for root in proto.types.own
    ]

    for conversion in proto.conversions.own:
        sections.append(conversion.accept_r(OwnedConversionGenerator()))
        view_conversion = conversion.accept(ViewConversionGenerator())
        if view_conversion is not None:
            sections.append(view_conversion)

    return cg.File(
        includes=[
            cg.Include("cstdint", system=True),
            cg.Include("cstring", system=True),
            cg.Include("string", system=True),
            cg.Include("string_view", system=True),
            cg.Include("initializer_list", system=True),
            cg.Include("array", system=True),
            cg.Include("vector", system=True),
            cg.Include("variant", system=True),
            cg.Include("stdexcept", system=True),
            cg.Include("optional", system=True),
            cg.Include("tako/tako.hh"),
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
                wrap_in_namespace(protocol_namespace(proto.name), cg.Section(sections)),
                cg.Raw("#pragma GCC diagnostic pop"),
            ]
        ),
        pragma_once=True,
    )


@dataclasses.dataclass
class RootConstantGenerator(kir.RootConstantVisitor[cg.Node]):
    def visit_int_constant(self, constant: kir.RootIntConstant) -> cg.Node:
        ctype = cint_type(constant.type_.width, constant.type_.sign)
        expr = cint_literal(constant.type_.width, constant.type_.sign, constant.value)
        return cg.Raw(f"constexpr {ctype} {constant.name.name()} = {expr};")

    def visit_string_constant(self, constant: kir.RootStringConstant) -> cg.Node:
        # We encode the string as JSON in an attempt to correctly escape it
        cstring = json.dumps(constant.value)
        return cg.Raw(f"constexpr const char* {constant.name.name()} = {cstring};")


@dataclasses.dataclass
class RootTypeGenerator(tir.RootTypeVisitor[cg.Node]):
    def visit_struct(self, root: tir.Struct) -> cg.Node:
        return cg.Section([gen_owned_class(root), gen_view_class(root)])

    def visit_variant(self, root: tir.Variant) -> cg.Node:
        return cg.Section([gen_owned_variant(root), gen_view_variant(root)])

    def visit_enum(self, root: tir.Enum) -> cg.Node:
        return gen_enum(root)


def gen_owned_class(struct: tir.Struct) -> cg.Node:
    class_name = OwnedCppType.get_local_struct(struct)
    builder = ClassBuilder()

    builder.public += [
        cg.Raw(f"{field.type_.accept(OwnedCppType())} {fname};")
        for fname, field in struct.get_owned()
    ]

    builder.add_parts(gen_serializer(struct))
    builder.add_parts(struct.size.accept(StructSizer(struct)))

    owned_fnames = [fname for fname, _ in struct.get_owned()]
    if not owned_fnames:
        eq_expr = "true"
    else:
        eq_expr = " && ".join([f"{x} == _other.{x}" for x in owned_fnames])
    builder.public.append(
        gen_raw(
            """\
        bool operator ==(const {{ class_name }}& _other) const {
            return {{ eq_expr }};
        }
        bool operator !=(const {{ class_name }}& _other) const {
            return !(*this == _other);
        }""",
            locals(),
        )
    )

    return cg.Class(name=class_name, bases=[], sections=builder.finalize())


def gen_serializer(struct: tir.Struct) -> ClassParts:
    builder_parts: t.List[cg.Node] = []
    helpers: t.List[cg.Node] = []
    for fname, field in struct.get_non_virtual():
        # If the field is a dependent field, generate its value from some other field
        if field.master_field is not None:
            if field.master_field.key_property == tir.KeyProperty.VARIANT_TAG:
                fvalue_expr = f"{field.master_field.master_field}.tag()"
            elif field.master_field.key_property == tir.KeyProperty.SEQ_LENGTH:
                fvalue_expr = f"{field.master_field.master_field}.size()"
            else:
                assert_never(field.master_field.key_property)
        else:
            fvalue_expr = f"{fname}"
        builder_parts.append(
            cg.Raw(
                f"buf = {field.type_.accept(ViewCppType())}::serialize_into({fvalue_expr}, buf);"
            )
        )
    builder_parts.append(cg.Raw(f"return buf;"))

    return ClassParts(
        cg.Function(
            "serialize_into",
            [(cg.Type("::gsl::span<::gsl::byte>"), "buf")],
            cg.Type("::gsl::span<::gsl::byte>"),
            cg.Section(builder_parts),
            const=True,
        ),
        cg.Section(helpers),
    )


@dataclasses.dataclass
class StructSizer(st.SizeVisitor[ClassParts]):
    struct: tir.Struct

    def visit_constant(self, size: st.Constant) -> ClassParts:
        return ClassParts(
            gen_raw(
                """\
                static constexpr size_t SIZE_BYTES = {{ size.value }};
                using Buffer = ::std::array<::gsl::byte, {{ size.value }}>;
                constexpr size_t size_bytes() const {
                    return SIZE_BYTES;
                }
                Buffer serialize() const {
                    Buffer result;
                    serialize_into(result);
                    return result;
                }""",
                locals(),
            )
        )

    def visit_dynamic(self, size: st.Dynamic) -> ClassParts:
        size_sum = st.SizeSum.zero()
        for fname, field in self.struct.get_non_virtual():
            size_sum = size_sum.add(fname, field.type_.size)

        size_parts = [str(size_sum.base)] + [
            f"{self.struct.fields[fname].type_.accept(ViewCppType())}::size_bytes({fname})"
            for fname in size_sum.names
        ]
        size_expr = " + ".join(size_parts)
        return ClassParts(
            gen_raw(
                """\
                using Buffer = ::std::vector<::gsl::byte>;
                size_t size_bytes() const {
                    return {{ size_expr }};
                }
                Buffer serialize() const {
                    Buffer result{size_bytes()};
                    serialize_into(result);
                    return result;
                }""",
                locals(),
            )
        )


def gen_view_class(struct: tir.Struct) -> cg.Node:
    class_name = ViewCppType.get_local_struct(struct)
    owned_type = OwnedCppType.get_local_struct(struct)
    builder = ClassBuilder()

    if isinstance(struct.size, st.Constant):
        builder.public.append(
            cg.Raw(f"static constexpr size_t SIZE_BYTES = {struct.size.value};")
        )

    builder_info = [
        (fname, field.type_.accept(ViewCppType()))
        for fname, field in struct.get_owned()
    ]
    builder.public.append(
        gen_raw(
            """\
            using Rendered = {{ class_name }};
            using Built = {{ owned_type }};
            static Built build(const Rendered& rendered) {
                return Built {
                {%- for fname, fctype in builder_info %}
                    .{{ fname }} = {{ fctype }}::build(rendered.{{ fname }}()),
                {%- endfor %}
                };
            }
            Built build() const {
                return build(*this);
            }""",
            locals(),
        )
    )
    builder.public.append(gen_render(struct))
    builder.public.append(gen_parse(struct))
    builder.public.append(
        gen_raw(
            """\
            static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
                return built.serialize_into(buf);
            }
            static size_t size_bytes(const Built& built) {
                return built.size_bytes();
            }""",
            locals(),
        )
    )
    builder.public += [
        gen_raw_getter(fname, field) for fname, field in struct.get_non_virtual()
    ]
    # Virtual fields get getters, but not raw getters.
    builder.public += [
        gen_getter(fname, field) for fname, field in struct.fields.items()
    ]
    builder.public.append(
        gen_raw(
            """\
            ::gsl::span<const ::gsl::byte> backing_buffer() const {
                return _buf;
            }""",
            locals(),
        )
    )

    member_info = [("_buf", "::gsl::span<const ::gsl::byte>")] + [
        (f"_info_{fname}", f"::tako::ParseInfo<{field.type_.accept(ViewCppType())}>")
        for fname, field in struct.get_non_virtual_dynamic()
    ]
    builder.private += [
        gen_raw(
            """\
            explicit {{ class_name }}({%- for name, ctype in member_info -%}
                {{ ctype }} _cons{{ name }}{{ ", " if not loop.last }}
                {%- endfor -%}) :
            {%- for name, _ in member_info -%}
                {{ name }}{ _cons{{ name }} }{{ "," if not loop.last }}
            {%- endfor -%} {}
            {%- for name, ctype in member_info%}
            {{ ctype }} {{ name }};
            {%- endfor %}""",
            locals(),
        )
    ]

    return cg.Class(name=class_name, bases=[], sections=builder.finalize())


def gen_getter(fname: str, field: tir.Field) -> cg.Node:
    ctype = field.type_.accept(ViewCppType())

    def resolve_arg(x: t.Union[int, str]) -> str:
        if isinstance(x, int):
            return str(x)
        elif isinstance(x, str):
            return f"{x}()"
        else:
            assert_never(x)

    if isinstance(field.type_, tir.Virtual):
        src_buf_expr = "_virtual_buf"
        getter_arg = f"::gsl::span<const ::gsl::byte> {src_buf_expr}"
        func = "parse"
        ret = f"::tako::ParseResult<{ctype}>"
    else:
        src_buf_expr = f"raw_{fname}()"
        getter_arg = ""
        func = "render"
        ret = f"{ctype}::Rendered"

    args = ", ".join([src_buf_expr] + resolve_field_args(resolve_arg, field.type_))
    return gen_raw(
        """\
    {{ ret }} {{ fname }}({{ getter_arg }}) const {
        return {{ ctype }}::{{ func }}({{ args }});
    }""",
        locals(),
    )


def gen_raw_getter(fname: str, field: tir.Field) -> cg.Node:
    offset_expr = cpp_offset_expr(field.offset, "_buf", "_info_", ".")
    return gen_raw(
        """\
    ::gsl::span<const ::gsl::byte> raw_{{ fname }}() const {
        return {{ offset_expr }};
    }""",
        locals(),
    )


def gen_render(struct: tir.Struct) -> cg.Node:
    body: t.List[cg.Node] = []
    body += [
        gen_render_block(struct, fname, "_buf", field)
        for fname, field in struct.get_non_virtual_dynamic()
    ]
    assignments = gen_render_assign(struct, "_buf", "")
    body += [
        gen_raw(
            """\
            return Rendered {
                {%- for src, value in assignments %}
                {{ value }}{{ "," if not loop.last }}
                {%- endfor %}
            };""",
            locals(),
        )
    ]

    return cg.Function(
        "render",
        [(cg.Type("::gsl::span<const ::gsl::byte>"), "_buf")],
        cg.Type(f"Rendered"),
        cg.Section(body),
        static=True,
    )


def gen_render_assign(
    struct: tir.Struct, buf_expr: str, fname_prefix: str
) -> t.List[t.Tuple[str, str]]:
    return [("_buf", buf_expr)] + [
        (f"_info_{fname}", f"::std::move({fname_prefix}{fname})")
        for fname, _ in struct.get_non_virtual_dynamic()
    ]


def gen_render_block(
    struct: tir.Struct, fname: str, src_buf: str, field: tir.Field
) -> cg.Node:
    def resolve_arg(x: t.Union[int, str]) -> str:
        if isinstance(x, int):
            return str(x)
        elif isinstance(x, str):
            argf = struct.fields[x]
            argctype = argf.type_.accept(ViewCppType())
            offset_expr = cpp_offset_expr(argf.offset, src_buf, "", ".")
            return f"{argctype}::render({offset_expr})"
        else:
            assert_never(x)

    fctype = field.type_.accept(ViewCppType())
    offset_expr = cpp_offset_expr(field.offset, src_buf, "", ".")
    args = ", ".join([offset_expr] + resolve_field_args(resolve_arg, field.type_))
    return cg.Raw(f"auto {fname} = {fctype}::parse({args}).value();")


def gen_parse(struct: tir.Struct) -> cg.Node:
    body: t.List[cg.Node] = []
    last_field_trivial = False
    for fname, field in struct.get_non_virtual():
        if not field.type_.trivial or field.master_field is not None:
            body.append(gen_parse_block(fname, field, "_buf"))
        last_field_trivial = field.type_.trivial
    if last_field_trivial:
        tail_offset_expr = cpp_offset_expr(struct.tail_offset, "_buf", "", "->")
        body.append(
            cg.Raw(
                f"""\
            if ({tail_offset_expr}.data() > _buf.end()) {{
                return {make_error(ParseError.NOT_ENOUGH_DATA)};
            }}"""
            )
        )
    assignments = [("_buf", "_initial_buf")] + [
        (f"_info_{fname}", f"::std::move({fname}->rendered)")
        for fname, _ in struct.get_non_virtual_dynamic()
    ]
    assignments = gen_render_assign(struct, "_buf", "*")
    if not struct.fields:
        tail_expr = "_buf"
    else:
        last_fname, last_field = list(struct.fields.items())[-1]
        tail_expr = cpp_offset_expr(struct.tail_offset, "_buf", "", "->")
    body += [
        gen_raw(
            """\
            return ::tako::ParseResult<Rendered>(tl::in_place,
                Rendered {
                    {%- for src, value in assignments %}
                    {{ value }}{{ "," if not loop.last }}
                    {%- endfor %}
                },
                {{ tail_expr  }}
            );
        """,
            locals(),
        )
    ]

    return cg.Function(
        "parse",
        [(cg.Type("::gsl::span<const ::gsl::byte>"), "_buf")],
        cg.Type(f"::tako::ParseResult<Rendered>"),
        cg.Section(body),
        static=True,
    )


def gen_parse_block(fname: str, field: tir.Field, src_buf: str) -> cg.Node:
    def resolve_arg(x: t.Union[int, str]) -> str:
        if isinstance(x, int):
            return str(x)
        elif isinstance(x, str):
            return f"{x}->rendered"
        else:
            assert_never(x)

    fctype = field.type_.accept(ViewCppType())
    args = ", ".join(
        [cpp_offset_expr(field.offset, src_buf, "", "->")]
        + resolve_field_args(resolve_arg, field.type_)
    )
    return gen_raw(
        """\
        auto {{ fname }} = {{ fctype }}::parse({{ args }});
        if (!{{ fname }}) {
            return ::tl::make_unexpected({{ fname }}.error());
        }
        """,
        locals(),
    )


def resolve_field_args(
    resolver: t.Callable[[t.Union[int, str]], str], type_: tir.Type
) -> t.List[str]:
    return [resolver(x) for x in type_.accept(FieldArgGenerator())]


@dataclasses.dataclass
class FieldArgGenerator(
    tir.TypeVisitor[t.List[t.Union[str, int]]], tir.LengthVisitor[t.Union[str, int]]
):
    def visit_int(self, type_: tir.Int) -> t.List[t.Union[str, int]]:
        return []

    def visit_float(self, type_: tir.Float) -> t.List[t.Union[str, int]]:
        return []

    def visit_array(self, type_: tir.Array) -> t.List[t.Union[str, int]]:
        return []

    def visit_vector(self, type_: tir.Vector) -> t.List[t.Union[str, int]]:
        return [self.handle_field_reference(type_.length)]

    def visit_list(self, type_: tir.List) -> t.List[t.Union[str, int]]:
        return [type_.length.accept(self)]

    def visit_fixed_length(self, length: tir.FixedLength) -> t.Union[str, int]:
        return length.length

    def visit_variable_length(self, length: tir.VariableLength) -> t.Union[str, int]:
        return self.handle_field_reference(length.length)

    def visit_detached_variant(
        self, type_: tir.DetachedVariant
    ) -> t.List[t.Union[str, int]]:
        return [self.handle_field_reference(type_.tag)]

    def visit_virtual(self, type_: tir.Virtual) -> t.List[t.Union[str, int]]:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> t.List[t.Union[str, int]]:
        return []

    def visit_variant(self, root: tir.Variant) -> t.List[t.Union[str, int]]:
        raise InternalError()

    def visit_enum(self, root: tir.Enum) -> t.List[t.Union[str, int]]:
        return []

    def handle_field_reference(self, fr: tir.FieldReference) -> t.Union[str, int]:
        return fr.name


def gen_owned_variant(root: tir.Variant) -> cg.Node:
    owned_ctype = root.accept(OwnedCppType())
    return gen_variant_class(
        root,
        OwnedCppType(),
        cg.Section(
            [
                gen_raw(
                    """\
            bool operator ==(const {{ owned_ctype }}& other) const {
                return value == other.value;
            }
            bool operator !=(const {{ owned_ctype }}& other) const {
                return value != other.value;
            }
            gsl::span<gsl::byte> serialize_into(gsl::span<gsl::byte> buf) const {
                return accept([&buf](auto&& x){
                    return x.serialize_into(buf);
                });
            }""",
                    locals(),
                ),
                root.size.accept(CommonVariantSizer()),
                root.size.accept(OwnedVariantSizer()),
            ]
        ),
    )


def gen_view_variant(root: tir.Variant) -> cg.Node:
    view_class_name = ViewCppType.get_local_variant(root)
    owned_ctype = root.accept(OwnedCppType())
    tag_ctype = root.tag_type.accept(OwnedCppType())
    variants = [
        (
            variant_type.accept(ViewCppType()),
            cint_literal(root.tag_type.width, root.tag_type.sign, tag_value),
        )
        for variant_type, tag_value in root.tags.items()
    ]
    return gen_variant_class(
        root,
        ViewCppType(),
        cg.Section(
            [
                gen_raw(
                    """\
                using Rendered = {{ view_class_name }};
                static Rendered render(gsl::span<const gsl::byte> buf, {{ tag_ctype }} tag) {
                    {%- for variant_type, tag_value in variants %}
                    if (tag == {{ tag_value }}) { return {{ variant_type }}::render(buf); }
                    {%- endfor %}
                    throw ::std::domain_error("input had illegal value");
                }
                using Built = {{ owned_ctype }};
                static Built build(const Rendered& rendered) {
                    return rendered.match(
                    {%- for vtype, _ in variants %}
                        [](const {{ vtype }}& x) -> Built { return {{ vtype }}::build(x); }{{ "," if not loop.last }}
                    {%- endfor %}
                    );
                }
                Built build() const {
                    return build(*this);
                }
                static ::tako::ParseResult<Rendered> parse(::gsl::span<const ::gsl::byte> buf, {{ tag_ctype }} tag) {
                    {%- for variant_type, tag_value in variants %}
                    if (tag == {{ tag_value }}) {
                        auto maybe = {{ variant_type }}::parse(buf);
                        if (!maybe) {
                            return tl::make_unexpected(maybe.error());
                        } else {
                            return ::tako::ParseResult<Rendered>(tl::in_place,
                                ::std::move(maybe->rendered),
                                maybe->tail
                            );
                        }
                    }
                    {%- endfor %}
                    return {{ make_error(ParseError.MALFORMED) }};
                }
                static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
                    return built.serialize_into(buf);
                }""",
                    locals(),
                ),
                root.size.accept(CommonVariantSizer()),
                root.size.accept(ViewVariantSizer()),
            ]
        ),
    )


# Generate a class with a variant as a member. This ensures that multiple variants
# of the same types are actually unique C++ types, which a using declaration
# would not.
# Subclassing a variant is not OK either -- see
# https://cplusplus.github.io/LWG/issue3052
# Regarding std::visit(Visitor&& visitor, Variants&&... variants),
# it says:
#     -?- Remarks: This function shall not participate in overload resolution unless
#     remove_cvref_t<Variantsi> is a specialization of variant for all 0 <= i < n.
# Another option would be to put a tag type into the variant, but then each visitor has to
# know about it.
# Making a custom class also lets us add nice functions like match() and tag().
def gen_variant_class(
    root: tir.Variant, type_gen: t.Union[ViewCppType, OwnedCppType], extra: cg.Node
) -> cg.Node:
    class_name = type_gen.get_local_variant(root)
    tag_ctype = root.tag_type.accept(OwnedCppType())
    variants = [
        (
            variant_type.accept(type_gen),
            cint_literal(root.tag_type.width, root.tag_type.sign, tag_value),
        )
        for variant_type, tag_value in root.tags.items()
    ]
    types = ", ".join([ctype for ctype, _ in variants])
    # The is_constructible is required, otherwise the constructor will clobber the default move and copy operators.
    return cg.Class(
        name=class_name,
        bases=[],
        sections=[
            (
                cg.Visibility.PUBLIC,
                cg.Section(
                    [
                        gen_raw(
                            """\
                        using V = ::std::variant<{{ types }}>;
                        V value;
                        template <typename T, typename=typename ::std::enable_if<::std::is_constructible<V, T>::value, T>::type>
                        {{ class_name }}(T&& t) : value{::std::forward<T>(t)} {}
                        template <typename... F>
                        auto match(F&&... args) {
                            return accept(::tako::overloaded{::std::forward<F>(args)...});
                        }
                        template <typename... F>
                        auto match(F&&... args) const {
                            return accept(::tako::overloaded{::std::forward<F>(args)...});
                        }
                        template <typename T>
                        auto accept(T&& visitor) {
                            return ::std::visit(::std::forward<T>(visitor), value);
                        }
                        template <typename T>
                        auto accept(T&& visitor) const {
                            return ::std::visit(::std::forward<T>(visitor), value);
                        }
                        template <typename R, typename... F>
                        auto match_unify(F&&... args) {
                            return accept_unify<R>(::tako::overloaded{::std::forward<F>(args)...});
                        }
                        template <typename R, typename... F>
                        auto match_unify(F&&... args) const {
                            return accept_unify<R>(::tako::overloaded{::std::forward<F>(args)...});
                        }
                        template <typename R, typename T>
                        auto accept_unify(T&& visitor) {
                            return ::std::visit(::tako::unify<R>(::std::forward<T>(visitor)), value);
                        }
                        template <typename R, typename T>
                        auto accept_unify(T&& visitor) const {
                            return ::std::visit(::tako::unify<R>(::std::forward<T>(visitor)), value);
                        }
                        template <typename T>
                        {{ optional_type }}<T*> get() {
                            auto x = ::std::get_if<T>(&value);
                            if (x) {
                                return x;
                            } else {
                                return {{ nullopt }};
                            }
                        }
                        template <typename T>
                        {{ optional_type }}<const T*> get() const {
                            auto x = ::std::get_if<T>(&value);
                            if (x) {
                                return x;
                            } else {
                                return {{ nullopt }};
                            }
                        }
                        {{ tag_ctype }} tag() const {
                            return match(
                            {%- for variant_type, tag_value in variants %}
                                [](const {{ variant_type }}&) { return {{ tag_value }}; }{{ "," if not loop.last }}
                            {%- endfor %}
                            );
                        }""",
                            locals(),
                        ),
                        extra,
                    ]
                ),
            )
        ],
    )


@dataclasses.dataclass
class CommonVariantSizer(st.SizeVisitor[cg.Node]):
    def visit_constant(self, size: st.Constant) -> cg.Node:
        return cg.Raw(f"static constexpr size_t SIZE_BYTES = {size.value};")

    def visit_dynamic(self, size: st.Dynamic) -> cg.Node:
        return cg.Raw("")


@dataclasses.dataclass
class OwnedVariantSizer(st.SizeVisitor[cg.Node]):
    def visit_constant(self, size: st.Constant) -> cg.Node:
        return gen_raw(
            """\
            constexpr size_t size_bytes() const {
                return SIZE_BYTES;
            }""",
            locals(),
        )

    def visit_dynamic(self, size: st.Dynamic) -> cg.Node:
        return gen_raw(
            """\
            size_t size_bytes() const {
                return accept([](auto&& x){
                    return x.size_bytes();
                });
            }""",
            locals(),
        )


@dataclasses.dataclass
class ViewVariantSizer(st.SizeVisitor[cg.Node]):
    def visit_constant(self, size: st.Constant) -> cg.Node:
        return gen_raw(
            """\
            static size_t size_bytes(const Built&) {
                return SIZE_BYTES;
            }""",
            locals(),
        )

    def visit_dynamic(self, size: st.Dynamic) -> cg.Node:
        return gen_raw(
            """\
            static size_t size_bytes(const Built& built) {
                return built.size_bytes();
            }""",
            locals(),
        )


def gen_enum(root: tir.Enum) -> cg.Node:
    class_name = ViewCppType.get_local_enum(root)
    builder = ClassBuilder()

    network = cint_type(root.underlying_type.width, Sign.UNSIGNED)
    underlying = cint_type(root.underlying_type.width, root.underlying_type.sign)
    cendianness = endianness_to_cpp(root.underlying_type.endianness)
    cenum = {
        name: cint_literal(root.underlying_type.width, root.underlying_type.sign, value)
        for name, value in root.variants.items()
    }
    ur = representable_range(root.underlying_type.width, root.underlying_type.sign)

    def gen_range_check(r: Range) -> str:
        start = cint_literal(
            root.underlying_type.width, root.underlying_type.sign, r.start
        )
        end = cint_literal(root.underlying_type.width, root.underlying_type.sign, r.end)
        if r.is_unit():
            return f"(value_ == {start})"
        parts = []
        if r.start != ur.start:
            parts.append(f"value_ >= {start}")
        if r.end != ur.stop - 1:
            parts.append(f"value_ <= {end}")
        return f"({' && '.join(parts)})"

    num_values = cint_literal(8, Sign.UNSIGNED, len(cenum))
    check = " || ".join(map(gen_range_check, root.valid_ranges))
    if not check:
        check = "false"
    public = gen_raw(
        """\
        using Underlying = {{ underlying }};
        {%- for name in root.variants.keys() %}
        static const {{ class_name }} {{ name }};
        {%- endfor %}
        static const ::std::array<{{ class_name }}, {{ num_values }}> VALUES;
        constexpr {{ underlying }} value() const {
            return value_;
        }
        constexpr ::std::string_view name() const {
            switch (value_) {
                {%- for name, value in cenum.items() %}
                case {{ value }}:
                    return "{{ name }}";
                {%- endfor %}
                default:
                    throw ::std::domain_error("input had illegal value");
            }
        }
        constexpr bool valid() {
            return {{ check }};
        }
        constexpr bool operator ==(const {{ class_name }}& other) const {
            return value_ == other.value_;
        }
        constexpr bool operator !=(const {{ class_name }}& other) const {
            return value_ != other.value_;
        }
        constexpr static {{ class_name }} make_unsafe({{ underlying }} value) {
            return {{ class_name }}{value};
        }
        static ::tl::expected<{{ class_name }}, ::tako::Unit> from_int({{ underlying }} value) {
            auto e = make_unsafe(value);
            if (e.valid()) {
                return e;
            } else {
                return ::tl::make_unexpected(::tako::Unit{});
            }
        }
        static ::tl::expected<{{ class_name }}, ::tako::Unit> from_str(::std::string_view value) {
            {%- for name, value in cenum.items() %}
            if (::std::string_view("{{ name }}") == value) {
                return make_unsafe({{ value }});
            }
            {%- endfor %}
            return ::tl::make_unexpected(::tako::Unit{});
        }

        static constexpr size_t SIZE_BYTES = sizeof({{ underlying }});
        using Rendered = {{ class_name }};
        static Rendered render(::gsl::span<const gsl::byte> buf) {
            return make_unsafe(::tako::PrimitiveConverter<{{ underlying }}, {{ cendianness }}>::from_network(buf));
        }
        using Built = {{ class_name }};
        static Built build(const Rendered& rendered) {
            return rendered;
        }
        static ::tako::ParseResult<Rendered> parse(gsl::span<const gsl::byte> buf) {
            auto tail = ::tako::unsafe_subspan(buf, sizeof({{ underlying }}));
            if (tail.data() > buf.end()) {
                return {{ make_error(ParseError.NOT_ENOUGH_DATA) }};
            } else if (!render(buf).valid()) {
                return {{ make_error(ParseError.MALFORMED) }};
            } else {
                return ::tako::ParseResult<Rendered>(tl::in_place,
                    render(buf),
                    tail
                );
            }
        }

        static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
            return ::tako::PrimitiveConverter<{{ underlying }}, {{ cendianness }}>::to_network(built.value_, buf);
        }
        static constexpr size_t size_bytes(const Built&) { return SIZE_BYTES; }""",
        locals(),
    )
    private = gen_raw(
        """\
        constexpr {{ class_name }}({{ underlying }} value) : value_{value} {}
        {{ underlying }} value_;""",
        locals(),
    )

    builder.add_parts(ClassParts(public, private))
    enum_class = cg.Class(name=class_name, bases=[], sections=builder.finalize())

    value_names = ", ".join([f"{class_name}::{name}" for name in cenum.keys()])
    # This constexpr trick needs c++ 17 for inline constexpr
    # See https://stackoverflow.com/questions/38043442/how-do-inline-variables-work
    return cg.Section(
        [
            enum_class,
            gen_raw(
                """\
            {%- for name, value in cenum.items() %}
            constexpr {{ class_name }} {{ class_name }}::{{ name }} { {{ value }} };
            {%- endfor %}
            constexpr ::std::array<{{ class_name }}, {{ num_values }}> {{ class_name }}::VALUES{ {{ value_names }} };
            """,
                locals(),
            ),
        ]
    )


def get_conversion_types(
    conversion: cir.Conversion, typer: t.Union[ViewCppType, OwnedCppType]
) -> t.Tuple[str, str]:
    return conversion.src.accept(typer), conversion.target.accept(typer)


def get_owned_conversion_types(conversion: cir.Conversion) -> t.Tuple[str, str, str]:
    src, target = (
        conversion.src.accept(OwnedCppType()),
        conversion.target.accept(OwnedCppType()),
    )
    if conversion.strength < cir.ConversionStrength.TOTAL:
        ret = f"{optional_type}<{target}>"
    else:
        ret = target
    return src, target, ret


@dataclasses.dataclass
class OwnedConversionGenerator(cir.RootConversionVisitor[cg.Node]):
    def visit_enum_conversion(self, conversion: cir.EnumConversion) -> cg.Node:
        src_ctype, target_ctype, return_ctype = get_owned_conversion_types(conversion)

        return gen_raw(
            """\
            inline {{ return_ctype }} convert(const {{ src_ctype }}& src, ::tako::Type<{{ target_ctype }}>) {
                {%- for evm in conversion.mapping %}
                if (src == {{ src_ctype }}::{{ evm.src.name }}) {
                    {%- if evm.target is none %}
                    return {{ nullopt }};
                    {%- else %}
                    return {{ target_ctype }}::{{ evm.target.name }};
                    {%- endif %}
                }
                {%- endfor %}
                throw ::std::domain_error("input had illegal value");
            }""",
            locals(),
        )

    def visit_struct_conversion(self, conversion: cir.StructConversion) -> cg.Node:
        src_ctype, target_ctype, return_ctype = get_owned_conversion_types(conversion)

        conversion_exprs: t.List[t.Tuple[str, str, t.Tuple[str, bool]]] = []
        for fname, field in conversion.target.get_owned():
            conversion_exprs.append(
                (
                    fname,
                    field.type_.accept(OwnedCppType()),
                    conversion.mapping[fname].accept(
                        OwnedConversionExpressionGenerator("src")
                    ),
                )
            )

        return gen_raw(
            """\
            inline {{ return_ctype }} convert(const {{ src_ctype }}& src, ::tako::Type<{{ target_ctype }}>) {
                {%-for field_name, field_ctype, (conversion_expr, partial) in conversion_exprs %}
                {%- if partial %}
                {{ optional_type }}<{{ field_ctype }}> {{ field_name }} = {{ conversion_expr }};
                if (!{{ field_name }}) {
                    return {{ nullopt }};
                }
                {%- else %}
                {{ field_ctype }} {{ field_name }} = {{ conversion_expr }};
                {%- endif %}
                {%-endfor %}

                return {{ target_ctype }} {
                {%-for field_name, _, (_, partial) in conversion_exprs %}
                    {%- if partial %}
                    .{{ field_name }} = *{{ field_name }},
                    {%- else %}
                    .{{ field_name }} = {{ field_name }},
                    {%- endif %}
                {%-endfor %}
                };
            }""",
            locals(),
        )

    def visit_variant_conversion(self, conversion: cir.VariantConversion) -> cg.Node:
        src_ctype, target_ctype, return_ctype = get_owned_conversion_types(conversion)

        visitors = []
        for vvm in conversion.mapping:
            variant_ctype = vvm.src.type_.accept(OwnedCppType())
            if vvm.target is None:
                conversion_expr = None
                converted_ctype = None
            else:
                conversion_expr = (
                    vvm.target.conversion.accept(
                        OwnedConversionExpressionGenerator("x")
                    ),
                    vvm.target.conversion.strength == cir.ConversionStrength.PARTIAL,
                )
                converted_ctype = vvm.target.target.type_.accept(OwnedCppType())
            visitors.append((variant_ctype, conversion_expr, converted_ctype))

        return gen_raw(
            """\
            inline {{ return_ctype }} convert(const {{ src_ctype }}& src, ::tako::Type<{{ target_ctype }}>) {
                return src.match(
                    {%- for variant_ctype, conversion_expr, converted_ctype in visitors %}
                    [&](const {{ variant_ctype }}& x) -> {{ return_ctype }} {
                        {%- if conversion_expr is none %}
                        return {{ nullopt }};
                        {%- else %}
                        {%- if conversion_expr[1] %}
                        {{ optional_type }}<{{ converted_ctype }}> conv = {{ conversion_expr[0] }};
                        if (!conv) {
                            return {{ nullopt }};
                        } else {
                            return  {{ target_ctype }}{*conv};
                        }
                        {%- else %}
                            return  {{ target_ctype }}{ {{ conversion_expr[0] }} };
                        {%- endif %}
                        {%- endif %}
                    }{{ "," if not loop.last }}
                    {%- endfor %}
                );
            }""",
            locals(),
        )


@dataclasses.dataclass
class OwnedConversionExpressionGenerator(
    cir.ConversionVisitor[str], cir.FieldConversionVisitor[t.Tuple[str, bool]]
):
    src_expr: str

    def visit_identity_conversion(self, conversion: cir.IdentityConversion) -> str:
        return self.src_expr

    def root_conversion_expr(self, conversion: cir.RootConversion) -> str:
        fname = qname_to_cpp(
            protocol_namespace(conversion.protocol).with_name("convert")
        )
        target_ctype = conversion.target.accept(OwnedCppType())
        return f"{fname}({self.src_expr}, ::tako::Type<{target_ctype}>{{}})"

    def visit_enum_conversion(self, conversion: cir.EnumConversion) -> str:
        return self.root_conversion_expr(conversion)

    def visit_struct_conversion(self, conversion: cir.StructConversion) -> str:
        return self.root_conversion_expr(conversion)

    def visit_int_default_field_conversion(
        self, conversion: cir.IntDefaultFieldConversion
    ) -> t.Tuple[str, bool]:
        return (
            cint_literal(
                conversion.type_.width, conversion.type_.sign, conversion.value
            ),
            False,
        )

    def visit_enum_default_field_conversion(
        self, conversion: cir.EnumDefaultFieldConversion
    ) -> t.Tuple[str, bool]:
        ctype = conversion.type_.accept(OwnedCppType())
        return f"{ctype}::{conversion.value.name}", False

    def visit_transform_field_conversion(
        self, conversion: cir.TransformFieldConversion
    ) -> t.Tuple[str, bool]:
        inner_src_expr = f"{self.src_expr}.{conversion.src_field}"
        return (
            conversion.conversion.accept(
                OwnedConversionExpressionGenerator(inner_src_expr)
            ),
            conversion.conversion.strength == cir.ConversionStrength.PARTIAL,
        )

    def visit_variant_conversion(self, conversion: cir.VariantConversion) -> str:
        return self.root_conversion_expr(conversion)


@dataclasses.dataclass
class ViewConversionGenerator(cir.ConversionVisitor[t.Optional[cg.Node]]):
    def visit_identity_conversion(self, conversion: cir.IdentityConversion) -> cg.Node:
        raise InternalError()

    def visit_enum_conversion(
        self, conversion: cir.EnumConversion
    ) -> t.Optional[cg.Node]:
        # There are no enum views, don't need to generate anything
        return None

    def visit_struct_conversion(
        self, conversion: cir.StructConversion
    ) -> t.Optional[cg.Node]:
        # If the conversion is compatible, generate a conversion between the view types
        # Otherwise emit nothing
        if conversion.strength < cir.ConversionStrength.COMPATIBLE:
            return None

        src_ctype = conversion.src.accept(ViewCppType())
        target_ctype = conversion.target.accept(ViewCppType())

        # You take the buffer under the old type, and parse it as the new type.
        # You need to parse it again to resolve any-variable length fields.
        # But this will do more bounds checks then needed.
        return gen_raw(
            """\
            inline {{ target_ctype }} convert(const {{ src_ctype }}& src, ::tako::Type<{{ target_ctype }}>) {
                return {{ target_ctype }}::render(src.backing_buffer());
            }""",
            locals(),
        )

    def visit_variant_conversion(
        self, conversion: cir.VariantConversion
    ) -> t.Optional[cg.Node]:
        # TODO: this is annoying, but would be nice
        return None


def cpp_offset_expr(
    offset: st.Offset,
    base_buf: str,
    field_access_prefix: str,
    tail_access_operator: str,
) -> str:
    if offset.base is None:
        offset_base = base_buf
    else:
        offset_base = f"{field_access_prefix}{offset.base}{tail_access_operator}tail"
    return f"::tako::unsafe_subspan({offset_base}, {offset.offset})"


def gen_raw(template: str, env: t.Dict[str, t.Any]) -> cg.Raw:
    return cg.Raw(template_raw(template, {**globals(), **env}))
