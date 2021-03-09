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
import argparse
from pathlib import Path
from tako.core.sir import Protocol, tir, kir, cir
import tako.core.size_types as st
import more_itertools
from tako.util.ranges import Range
from tako.generators.java import java_gen as jg
from tako.generators.generator import Generator
from tako.util.cast import assert_never
from tako.util.pretty_printer import PrettyPrinter
from tako.generators.template import template_raw
from tako.util.int_model import Sign, Endianness, representable_range
from tako.util.qname import QName
from tako.core.internal_error import InternalError
from tako.util.name_format import snake_to_camel, snake_to_pascal

tako_pkg = "tako"
parse_exception = f"{tako_pkg}.ParseException"
conversion_exception = f"{tako_pkg}.ConversionException"
fastutil = "it.unimi.dsi.fastutil"
arraylist = "java.util.ArrayList"
byte_buffer = "java.nio.ByteBuffer"
primitives = ["byte", "short", "int", "long", "float", "double", "boolean", "char"]


class JavaGenerator(Generator):
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def generate_into(self, proto: Protocol, out_dir: Path, args: t.Any) -> None:
        proto_file = out_dir / java_relative_path(proto.name)
        proto_file.parent.mkdir(parents=True, exist_ok=True)
        with proto_file.open("w") as out:
            java_node = generate(proto)
            printer = PrettyPrinter(4, out)
            java_node.pretty_printer(printer)

    def list_outputs(
        self, proto_qname: QName, args: t.Any
    ) -> t.Generator[Path, None, None]:
        return
        yield


def java_relative_path(qname: QName) -> Path:
    return Path(*qname.namespace().parts) / Path(f"{qname.name()}.java")


def generate(proto: Protocol) -> jg.Node:
    sections: t.List[jg.Node] = []
    sections += [
        constant.accept(RootConstantGenerator())
        for constant in proto.constants.constants.values()
    ]
    sections += [
        proto.types.types[root].accept_rtv(RootTypeGenerator())
        for root in proto.types.own
    ]
    for conversion in proto.conversions.own:
        sections.append(conversion.accept_r(BuiltConversionGenerator()))
        view_conversion = conversion.accept(ViewConversionGenerator())
        if view_conversion is not None:
            sections.append(view_conversion)
    result: t.List[jg.Node] = []
    result.append(jg.Raw(f"package {proto.name.namespace()};"))
    # result += [jg.Raw(f"import {ext};") for ext in proto.types.external_protocols]
    result.append(jg.Class(proto.name.name(), body=jg.Section(sections)))
    return jg.Section(result)


@dataclasses.dataclass
class RootConstantGenerator(kir.RootConstantVisitor[jg.Node]):
    def visit_int_constant(self, constant: kir.RootIntConstant) -> jg.Node:
        jtype = jint_type(constant.type_.width)
        expr = jint_literal(constant.type_.width, constant.value)
        return jg.Raw(f"public static final {jtype} {constant.name.name()} = {expr};")

    def visit_string_constant(self, constant: kir.RootStringConstant) -> jg.Node:
        cstring = json.dumps(constant.value)
        return jg.Raw(
            f"public static final java.lang.String {constant.name.name()} = {cstring};"
        )


@dataclasses.dataclass
class RootTypeGenerator(tir.RootTypeVisitor[jg.Node]):
    def visit_struct(self, root: tir.Struct) -> jg.Node:
        return jg.Section(
            [
                gen_struct_context(root),
                gen_built_struct(root),
                gen_view_struct(root),
                gen_struct_type_class(root),
            ]
        )

    def visit_variant(self, root: tir.Variant) -> jg.Node:
        return jg.Section(
            [
                gen_variant_context(root),
                gen_built_variant(root),
                gen_view_variant(root),
                gen_variant_type_class(root),
            ]
        )

    def visit_enum(self, root: tir.Enum) -> jg.Node:
        return jg.Section([gen_enum(root), gen_enum_type_class(root)])


def gen_struct_context(struct: tir.Struct) -> jg.Node:
    return jg.Class(
        name=JavaTypeContext.get_local_struct(struct),
        body=jg.Section(
            [
                jg.Raw(
                    f"public static final {field.type_.accept(JavaType())} {fname} = {field.type_.accept(JavaTypeInstance())};"
                )
                for fname, field in struct.fields.items()
            ]
        ),
        static=True,
    )


def gen_built_struct(struct: tir.Struct) -> jg.Node:
    class_name = BuiltJavaType.get_local_struct(struct)
    context = JavaTypeContext.get_local_struct(struct)
    parts: t.List[jg.Node] = []
    fields = [
        (fname, field.type_.accept(BuiltJavaType()), is_jprimitive(field.type_))
        for fname, field in struct.get_owned()
    ]

    for fname, jtype, primitive in fields:
        if not primitive:
            init = f" = {context}.{fname}.newBuilt()"
        else:
            init = ""
        parts.append(jg.Raw(f"private {jtype} {fname}{init};"))
    for fname, jtype, _ in fields:
        parts.append(
            jg.Raw(
                f"""\
            public {jtype} {snake_to_camel(fname)}() {{
                return this.{fname};
            }}
            public void {snake_to_camel("set_" + fname)}({jtype} target) {{
                this.{fname} = target;
            }}"""
            )
        )

    step_builder = []
    for (fname, field), (nf) in more_itertools.stagger(
        struct.get_owned(), offsets=(0, 1), longest=True
    ):
        if nf is None:
            next_builder = "Finisher<O>"
        else:
            nfname, _ = nf
            next_builder = f"Build{snake_to_pascal(nfname)}<O>"

        if isinstance(field.type_, tir.Struct) or isinstance(
            field.type_, tir.DetachedVariant
        ):
            out = f"{field.type_.accept(BuiltJavaType())}.Enterer<{next_builder}>"
            argtype = ""
            assign = ""
            ret = f"return this.work.{fname}.<{next_builder}>enterWith(this);"
        elif (
            isinstance(field.type_, tir.Int)
            or isinstance(field.type_, tir.Float)
            or isinstance(field.type_, tir.Enum)
        ):
            out = next_builder
            argtype = f"{field.type_.accept(BuiltJavaType())} x"
            assign = f"this.work.{fname} = x;"
            ret = f"return this;"
        else:
            out = next_builder
            fjtype = field.type_.accept(BuiltJavaType())
            argtype = f"java.util.function.Function<{fjtype}, {fjtype}> x"
            assign = f"this.work.{fname} = x.apply(this.work.{fname});"
            ret = f"return this;"
        step_builder.append(
            (
                f"Build{snake_to_pascal(fname)}",
                out,
                snake_to_camel(fname),
                argtype,
                assign,
                ret,
            )
        )
    step_builder.append((f"Finisher", "O", "finish", "", f"", f"return this.output;"))
    interfaces = list(more_itertools.first(zip(*step_builder))) + ["Setter", "Enterer"]
    interfaces_with_o = [f"{x}<O>" for x in interfaces]
    parts.append(
        gen_raw(
            """\
        {%- for cname, out, fname, argtype, _, _ in step_builder %}
        public static interface {{ cname }}<O> {
            {{ out }} {{ fname }}({{ argtype }});
        }
        {%- endfor %}
        public static interface Setter<O> {
            O set({{ class_name }} target);
        }
        public static interface Enterer<O> {
            {{ interfaces[0] }}<O> enter();
        }
        public static class Builder<O> implements {{ interfaces_with_o | join(", ") }} {
            private final {{ class_name }} work;
            private O output;
            public Builder({{ class_name }} work) {
                this.work = work;
                this.output = null;
            }
            public void setOutput(O output) {
                this.output = output;
            }
        {%- for cname, out, fname, argtype, assign, ret in step_builder %}
            public {{ out }} {{ fname }}({{ argtype }}) {
                {{ assign }}
                {{ ret }}
            }
        {%- endfor %}
            public O set({{ class_name }} target) {
                work.cloneInto(target);
                return output;
            }
            public {{ interfaces[0] }}<O> enter() {
                return work.<O>initWith(this.output);
            }
        }
        private final Builder<java.lang.Object> builder = new Builder<java.lang.Object>(this);
        @SuppressWarnings("unchecked")
        public {{ interfaces[0] }}<{{ class_name }}> init() {
            this.builder.setOutput(this);
            return ({{ interfaces[0] }}<{{ class_name }}>) ((java.lang.Object) this.builder);
        }
        @SuppressWarnings("unchecked")
        public <T> {{ interfaces[0] }}<T> initWith(T output) {
            this.builder.setOutput(output);
            return ({{ interfaces[0] }}<T>) ((java.lang.Object) this.builder);
        }
        @SuppressWarnings("unchecked")
        public <T> Enterer<T> enterWith(T output) {
            this.builder.setOutput(output);
            return (Enterer<T>) ((java.lang.Object) this.builder);
        }
        public static class Marker {}
        public static final Marker marker = new Marker();""",
            locals(),
        )
    )

    parts.append(gen_serializer(struct))
    parts.append(gen_sizer(struct))
    parts.append(
        gen_raw(
            """\
        public void cloneInto({{ class_name }} other) {
            {%- for fname, field in struct.get_owned() %}
            {%- if is_jprimitive(field.type_) %}
            this.{{ fname }} = other.{{ fname }};
            {%- else %}
            {{ context }}.{{ fname }}.cloneInto(this.{{ fname }}, other.{{ fname }});
            {%- endif %}
            {%- endfor %}
        }""",
            locals(),
        )
    )

    built_fnames = [fname for fname, _ in struct.get_owned()]
    if not built_fnames:
        eq_expr = "true"
    else:
        eq_expr = " && ".join(
            [f"java.util.Objects.equals(this.{x}, castOther.{x})" for x in built_fnames]
        )
    hash_expr = ", ".join([f"this.{fname}" for fname in built_fnames])
    parts.append(
        jg.Raw(
            f"""\
        @Override
        public boolean equals(Object other) {{
            if (other == null || !(other instanceof {class_name})) {{
                return false;
            }}
            {class_name} castOther = ({class_name}) other;
            return {eq_expr};
        }}
        @Override
        public int hashCode() {{
            return java.util.Objects.hash({hash_expr});
        }}"""
        )
    )

    return jg.Class(name=class_name, body=jg.Section(parts), static=True)


def gen_serializer(struct: tir.Struct) -> jg.Node:
    parts: t.List[jg.Node] = []
    for fname, field in struct.get_non_virtual():
        # If the field is a dependent field, generate its value from some other field
        if field.master_field is not None:
            if field.master_field.key_property == tir.KeyProperty.VARIANT_TAG:
                fvalue_expr = f"this.{field.master_field.master_field}.tag()"
            elif field.master_field.key_property == tir.KeyProperty.SEQ_LENGTH:
                fvalue_expr = f"(({field.type_.accept(BuiltJavaType())}) this.{field.master_field.master_field}.size())"
            else:
                assert_never(field.master_field.key_property)
        else:
            fvalue_expr = f"this.{fname}"
        parts.append(
            jg.Raw(
                f"offset = {JavaTypeContext.get_local_struct(struct)}.{fname}.serializeInto({fvalue_expr}, buf, offset);"
            )
        )
    parts.append(jg.Raw(f"return offset;"))

    return jg.Function(
        "public",
        "serializeInto",
        [(jg.Type(byte_buffer), "buf"), (jg.Type("int"), "offset")],
        jg.Type("int"),
        jg.Section(parts),
    )


def gen_sizer(struct: tir.Struct) -> jg.Node:
    size_sum = st.SizeSum.zero()
    for fname, field in struct.get_non_virtual():
        size_sum = size_sum.add(fname, field.type_.size)

    size_expr = " + ".join(
        [str(size_sum.base)]
        + [
            f"{JavaTypeContext.get_local_struct(struct)}.{fname}.sizeBytes(this.{fname})"
            for fname in size_sum.names
        ]
    )
    return jg.Raw(
        f"""\
        public int sizeBytes() {{
            return {size_expr};
        }}
        public {byte_buffer} serialize() {{
            {byte_buffer} result = {byte_buffer}.allocate(sizeBytes());
            serializeInto(result, 0);
            return result;
        }}"""
    )


def gen_view_struct(struct: tir.Struct) -> jg.Node:
    class_name = RenderedJavaType.get_local_struct(struct)
    built_type = BuiltJavaType.get_local_struct(struct)
    context = JavaTypeContext.get_local_struct(struct)

    parts: t.List[jg.Node] = []
    parts += [
        jg.Raw(f"private {byte_buffer} buf = null;"),
        jg.Raw(f"private int offset = 0;"),
    ]
    parts += [
        jg.Raw(
            f"private {field.type_.accept(RenderedJavaType())} view_{fname} = {context}.{fname}.newRendered();"
        )
        for fname, field in struct.get_non_virtual()
        if not is_jprimitive(field.type_)
    ]
    parts += [
        jg.Raw(f"private int offset_{fname} = 0;")
        for fname, _ in struct.get_non_virtual_dynamic()
    ]

    builder_info = [
        (fname, is_jprimitive(field.type_)) for fname, field in struct.get_owned()
    ]
    parts.append(
        gen_raw(
            """\
            public void build({{ built_type }} out) {
                {%- for fname, primitive in builder_info %}
                {%- if primitive %}
                out.{{ snake_to_camel("set_" + fname) }}(this.{{ snake_to_camel(fname) }}());
                {%- else %}
                {{ context }}.{{ fname }}.build(out.{{ snake_to_camel(fname) }}(), this.{{ snake_to_camel(fname) }}());
                {%- endif %}
                {%- endfor %}
            }""",
            locals(),
        )
    )
    parts.append(gen_render(struct))
    parts.append(gen_parse(struct))
    parts += [
        gen_getter(fname, field, context) for fname, field in struct.fields.items()
    ]
    parts.append(
        jg.Raw(
            f"""\
            public {byte_buffer} backingBuffer() {{
                return this.buf;
            }}
            public int backingBufferOffset() {{
                return this.offset;
            }}"""
        )
    )

    return jg.Class(name=class_name, body=jg.Section(parts), static=True)


def gen_getter(fname: str, field: tir.Field, context: str) -> jg.Node:
    def resolve_arg(x: t.Union[int, str]) -> str:
        if isinstance(x, int):
            return str(x)
        elif isinstance(x, str):
            return f"this.{snake_to_camel(x)}()"
        else:
            assert_never(x)

    jtype = field.type_.accept(RenderedJavaType())

    if isinstance(field.type_, tir.Virtual):
        if is_jprimitive(field.type_.inner):
            value_expr = f"{context}.{fname}.parse(buf, offset)"
            ret = jtype
            out_arg = ""
            ret_stmt = "return "
        else:
            args = ", ".join(
                ["out", "buf", "offset"] + resolve_field_args(resolve_arg, field.type_)
            )
            value_expr = f"{context}.{fname}.parse({args})"
            ret = "void"
            out_arg = f"{jtype} out, "
            ret_stmt = ""
        return jg.Raw(
            f"""\
            public {ret} {snake_to_camel(fname)}({out_arg}{byte_buffer} buf, int offset) throws {parse_exception} {{
                {ret_stmt}{value_expr};
            }}"""
        )
    else:
        offset_expr = cpp_offset_expr(field.offset, "this.offset", "this.offset_")
        if is_jprimitive(field.type_):
            body = f"return {context}.{fname}.render(this.buf, {offset_expr});"
        else:
            out = f"this.view_{fname}"
            args = ", ".join(
                [out, "this.buf", offset_expr]
                + resolve_field_args(resolve_arg, field.type_)
            )
            body = f"{context}.{fname}.render({args}); return {out};"
        return jg.Raw(
            f"""\
            public {jtype} {snake_to_camel(fname)}() {{
                {body}
            }}"""
        )


def struct_arg_resolver(
    struct: tir.Struct, src_buf: str, base_offset: str, offset_prefix: str
) -> t.Callable[[t.Union[int, str]], str]:
    def result(x: t.Union[int, str]) -> str:
        if isinstance(x, int):
            return str(x)
        elif isinstance(x, str):
            # This field has to be of integer type, so it can be rendered like this
            argf = struct.fields[x]
            offset_expr = cpp_offset_expr(argf.offset, base_offset, offset_prefix)
            return f"{JavaTypeContext.get_local_struct(struct)}.{x}.render({src_buf}, {offset_expr})"
        else:
            assert_never(x)

    return result


def gen_render(struct: tir.Struct) -> jg.Node:
    body: t.List[jg.Node] = []
    body += [
        gen_render_block(
            struct, fname, field, "this.buf", "this.offset", "this.offset_"
        )
        for fname, field in struct.get_non_virtual_dynamic()
    ]
    body.append(
        jg.Raw(
            """\
        this.buf = buf;
        this.offset = offset;"""
        )
    )

    return jg.Function(
        "public",
        "render",
        [(jg.Type(byte_buffer), "buf"), (jg.Type("int"), "offset")],
        jg.Type(f"void"),
        jg.Section(body),
    )


def gen_render_block(
    struct: tir.Struct,
    fname: str,
    field: tir.Field,
    src_buf: str,
    src_offset: str,
    offset_prefix: str,
) -> jg.Node:
    context = JavaTypeContext.get_local_struct(struct)
    offset_expr = cpp_offset_expr(field.offset, src_offset, offset_prefix)
    args = ", ".join(
        [src_buf, offset_expr]
        + resolve_field_args(
            struct_arg_resolver(struct, src_buf, src_offset, offset_prefix), field.type_
        )
    )
    return jg.Raw(
        f"""\
        try {{
            this.offset_{fname} = {context}.{fname}.parse(this.view_{fname}, {args});
        }} catch ({parse_exception} e) {{
            throw new java.lang.RuntimeException(e);
        }}"""
    )


def gen_parse(struct: tir.Struct) -> jg.Node:
    body: t.List[jg.Node] = []
    body.append(
        jg.Raw(
            f"""\
        this.buf = buf;
        this.offset = offset;"""
        )
    )
    last_field_trivial = False
    for fname, field in struct.get_non_virtual():
        if not field.type_.trivial or field.master_field is not None:
            body.append(
                gen_parse_block(
                    struct, fname, field, "this.buf", "this.offset", "this.offset_"
                )
            )
        last_field_trivial = field.type_.trivial
    if last_field_trivial:
        tail_offset_expr = cpp_offset_expr(
            struct.tail_offset, "this.offset", "this.offset_"
        )
        body.append(
            gen_raw(
                """\
            if ({{ tail_offset_expr }} > buf.limit()) {
                throw new {{ parse_exception }}.NotEnoughData();
            }""",
                locals(),
            )
        )
    if not struct.fields:
        tail_expr = "this.offset"
    else:
        tail_expr = cpp_offset_expr(struct.tail_offset, "this.offset", "this.offset_")
    body.append(jg.Raw(f"return {tail_expr};"))

    return jg.Function(
        "public",
        "parse",
        [(jg.Type(byte_buffer), "buf"), (jg.Type("int"), "offset")],
        jg.Type(f"int"),
        jg.Section(body),
        throws=[parse_exception],
    )


def gen_parse_block(
    struct: tir.Struct,
    fname: str,
    field: tir.Field,
    src_buf: str,
    src_offset: str,
    offset_prefix: str,
) -> jg.Node:
    context = JavaTypeContext.get_local_struct(struct)
    offset_expr = cpp_offset_expr(field.offset, src_offset, offset_prefix)
    args = ", ".join(
        [src_buf, offset_expr]
        + resolve_field_args(
            struct_arg_resolver(struct, src_buf, src_offset, offset_prefix), field.type_
        )
    )
    if is_jprimitive(field.type_):
        return jg.Raw(f"{context}.{fname}.parse({src_buf}, {offset_expr});")

    if isinstance(field.type_.size, st.Dynamic):
        result_expr = f"{offset_prefix}{fname} = "
    else:
        result_expr = ""

    return jg.Raw(f"{result_expr}{context}.{fname}.parse(this.view_{fname}, {args});")


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


def gen_struct_type_class(struct: tir.Struct) -> jg.Node:
    class_name = JavaType.get_local_struct(struct)
    view_class = RenderedJavaType.get_local_struct(struct)
    built_class = BuiltJavaType.get_local_struct(struct)
    fixed_size = isinstance(struct.size, st.Constant)
    if fixed_size:
        base = f"{tako_pkg}.FixedSizeTakoType"
    else:
        base = f"{tako_pkg}.SimpleTakoType"
    return gen_raw(
        """\
        public static class {{ class_name }} implements {{ base }}<{{ view_class }}, {{ built_class }}> {
            public {{ view_class }} newRendered() {
                return new {{ view_class }}();
            }
            public {{ built_class }} newBuilt() {
                return new {{ built_class }}();
            }
            public void render({{ view_class }} out, {{ byte_buffer }} buf, int offset) {
                out.render(buf, offset);
            }
            public int parse({{ view_class }} out, {{ byte_buffer }} buf, int offset) throws {{ parse_exception }}{
                return out.parse(buf, offset);
            }
            public void build({{ built_class }} out, {{ view_class }} rendered) {
                rendered.build(out);
            }
            public int serializeInto({{ built_class }} built, {{ byte_buffer }} buf, int offset) {
                return built.serializeInto(buf, offset);
            }
            public int sizeBytes({{ built_class }} built) {
                return built.sizeBytes();
            }
            {%- if fixed_size %}
            public int sizeBytes() {
                return {{ struct.size.value }};
            }
            {%- endif %}
            public void cloneInto({{ built_class }} out, {{ built_class }} src) {
                out.cloneInto(src);
            }
        }""",
        locals(),
    )


def format_vartag_int(x: int) -> str:
    if x < 0:
        return f"n{abs(x)}"
    else:
        return f"p{abs(x)}"


def gen_variant_context(root: tir.Variant) -> jg.Node:
    return jg.Class(
        name=JavaTypeContext.get_local_variant(root),
        body=jg.Section(
            [
                jg.Raw(
                    f"public static final {variant_type.accept(JavaType())} {format_vartag_int(tag_value)} = {variant_type.accept(JavaTypeInstance())};"
                )
                for variant_type, tag_value in root.tags.items()
            ]
        ),
        static=True,
    )


def gen_built_variant(root: tir.Variant) -> jg.Node:
    built_jtype = root.accept(BuiltJavaType())
    context = JavaTypeContext.get_local_variant(root)
    tag_jtype = root.tag_type.accept(BuiltJavaType())
    variants = [
        (
            format_vartag_int(tag_value),
            variant_type.accept(BuiltJavaType()),
            jint_literal(root.tag_type.width, tag_value),
        )
        for variant_type, tag_value in root.tags.items()
    ]
    return gen_variant_class(
        root,
        BuiltJavaType(),
        jg.Section(
            [
                gen_raw(
                    """\
            @Override
            public boolean equals(Object other) {
                if (other == null || ! (other instanceof {{ built_jtype }})) {
                    return false;
                }
                return java.util.Objects.equals(active, (({{ built_jtype }}) other).active);
            }
            @Override
            public int hashCode() {
                return java.util.Objects.hashCode(active);
            }
            public int serializeInto({{ byte_buffer }} buf, int offset) {
                {%- for vid, variant_type, _ in variants %}
                if (active instanceof {{ variant_type }}) {
                    return {{ context }}.{{ vid }}.serializeInto(({{ variant_type }}) active, buf, offset);
                }
                {%- endfor %}
                throw new java.lang.IllegalStateException("Illegal variant type: " + active.getClass().getName());
            }
            private final VoidVisitor cloneIntoVisitor = new VoidVisitor() {
                {%- for vid, variant_type, tag_value  in variants %}
                public void visit({{ variant_type }} x) {
                    {{ built_jtype }}.this.active = {{ built_jtype }}.this.{{ vid }};
                    {{ context }}.{{ vid }}.cloneInto({{ built_jtype }}.this.{{ vid }}, x);
                }
                {%- endfor %}
            };
            public void cloneInto({{ built_jtype }} other) {
                other.accept(cloneIntoVisitor);
            }
            public static interface Setter<O> {
                O set({{ built_jtype }} target);
            }
            public static interface Enterer<O> {
                VariantBuilder<O> enter();
            }
            public static interface Finisher<O> {
                O finish();
            }
            public static class VariantBuilder<O> implements Setter<O>, Enterer<O>, Finisher<O> {
                private final {{ built_jtype }} work;
                private O output;
                public VariantBuilder({{ built_jtype }} work) {
                    this.work = work;
                    this.output = null;
                }
                public void setOutput(O output) {
                    this.output = output;
                }
                {%- for vid, variant_type, _ in variants %}
                public {{ variant_type }}.Enterer<Finisher<O>> set({{ variant_type }}.Marker x) {
                    work.active = work.{{ vid }};
                    return work.{{ vid }}.enterWith(this);
                }
                {%- endfor %}
                public O finish() {
                    return this.output;
                }
                public O set({{ built_jtype }} target) {
                    work.cloneInto(target);
                    return output;
                }
                public VariantBuilder<O> enter() {
                    return work.<O>initWith(this.output);
                }
            }
            private final VariantBuilder<java.lang.Object> builder = new VariantBuilder<java.lang.Object>(this);
            @SuppressWarnings("unchecked")
            public VariantBuilder<{{ built_jtype }}> init() {
                this.builder.setOutput(this);
                return (VariantBuilder<{{ built_jtype }}>) ((java.lang.Object) this.builder);
            }
            @SuppressWarnings("unchecked")
            public <T> VariantBuilder<T> initWith(T output) {
                this.builder.setOutput(output);
                return (VariantBuilder<T>) ((java.lang.Object) this.builder);
            }
            @SuppressWarnings("unchecked")
            public <T> Enterer<T> enterWith(T output) {
                this.builder.setOutput(output);
                return (Enterer<T>) ((java.lang.Object) this.builder);
            }""",
                    locals(),
                ),
                root.size.accept(BuiltVariantSizer(root)),
            ]
        ),
    )


def gen_view_variant(root: tir.Variant) -> jg.Node:
    view_class_name = RenderedJavaType.get_local_variant(root)
    built_jtype = root.accept(BuiltJavaType())
    tag_jtype = root.tag_type.accept(BuiltJavaType())
    context = JavaTypeContext.get_local_variant(root)
    variants = [
        (
            format_vartag_int(tag_value),
            variant_type.accept(RenderedJavaType()),
            jint_literal(root.tag_type.width, tag_value),
            variant_type.accept(BuiltJavaType()),
        )
        for variant_type, tag_value in root.tags.items()
    ]
    return gen_variant_class(
        root,
        RenderedJavaType(),
        jg.Section(
            [
                gen_raw(
                    """\
                public void render({{ byte_buffer }} buf, int offset, {{ tag_jtype }} tag) {
                    {%- for vid, variant_type, tag_value, _ in variants %}
                    if (tag == {{ tag_value }}) {
                        active = {{ vid }};
                        {{ context }}.{{ vid }}.render(({{ variant_type }}) active, buf, offset);
                        return;
                    }
                    {%- endfor %}
                    throw new java.lang.IllegalStateException("Illegal tag: " + tag);
                }
                public int parse({{ byte_buffer }} buf, int offset,  {{ tag_jtype }} tag) throws {{ parse_exception }}{
                    {%- for vid, variant_type, tag_value, _ in variants %}
                    if (tag == {{ tag_value }}) {
                        active = {{ vid }};
                        return {{ context }}.{{ vid }}.parse(({{ variant_type }}) active, buf, offset);
                    }
                    {%- endfor %}
                    throw new {{ parse_exception }}.Malformed();
                }
                public void build({{ built_jtype }} out) {
                    {%- for vid, variant_type, _, built_type in variants %}
                    if (active instanceof {{ variant_type }}) {
                        {{ context }}.{{ vid }}.build(out.set({{ built_type }}.class), ({{ variant_type }}) active);
                    }
                    {%- endfor %}
                    throw new java.lang.IllegalStateException("Illegal variant type: " + active.getClass().getName());
                }""",
                    locals(),
                )
            ]
        ),
    )


def gen_variant_type_class(variant: tir.Variant) -> jg.Node:
    class_name = JavaType.get_local_variant(variant)
    view_class = RenderedJavaType.get_local_variant(variant)
    built_class = BuiltJavaType.get_local_variant(variant)
    tag_jtype = variant.tag_type.accept(BuiltJavaType())
    fixed_size = isinstance(variant.size, st.Constant)
    return gen_raw(
        """\
        public static class {{ class_name }} {
            public {{ view_class }} newRendered() {
                return new {{ view_class }}();
            }
            public {{ built_class }} newBuilt() {
                return new {{ built_class }}();
            }
            public void render({{ view_class }} out, {{ byte_buffer }} buf, int offset, {{ tag_jtype }} tag) {
                out.render(buf, offset, tag);
            }
            public int parse({{ view_class }} out, {{ byte_buffer }} buf, int offset, {{ tag_jtype }} tag) throws {{ parse_exception }}{
                return out.parse(buf, offset, tag);
            }
            public void build({{ built_class }} out, {{ view_class }} rendered) {
                rendered.build(out);
            }
            public int serializeInto({{ built_class }} built, {{ byte_buffer }} buf, int offset) {
                return built.serializeInto(buf, offset);
            }
            public int sizeBytes({{ built_class }} built) {
                return built.sizeBytes();
            }
            {%- if fixed_size %}
            public int sizeBytes() {
                return {{ variant.size.value }};
            }
            {%- endif %}
            public void cloneInto({{ built_class }} out, {{ built_class }} src) {
                out.cloneInto(src);
            }
        }""",
        locals(),
    )


def gen_variant_class(
    root: tir.Variant,
    type_gen: t.Union[RenderedJavaType, BuiltJavaType],
    extra: jg.Node,
) -> jg.Node:
    class_name = type_gen.get_local_variant(root)
    tag_jtype = root.tag_type.accept(BuiltJavaType())
    variants = [
        (
            format_vartag_int(tag_value),
            variant_type.accept(type_gen),
            jint_literal(root.tag_type.width, tag_value),
        )
        for variant_type, tag_value in root.tags.items()
    ]
    return jg.Class(
        name=class_name,
        body=jg.Section(
            [
                gen_raw(
                    """\
            public static interface Visitor<T> {
                {%- for _, variant_type, _ in variants %}
                T visit({{ variant_type }} x);
                {%- endfor %}
            }
            public static interface VoidVisitor {
                {%- for _, variant_type, _ in variants %}
                void visit({{ variant_type }} x);
                {%- endfor %}
            }
            {%- for primitive in primitives %}
            public static interface {{ primitive | capitalize }}Visitor {
                {%- for _, variant_type, _ in variants %}
                {{ primitive }} visit({{ variant_type }} x);
                {%- endfor %}
            }
            {%- endfor %}
            {%- for vid, variant_type, _ in variants %}
                private {{ variant_type }} {{ vid }} = new {{ variant_type }}();
            {%- endfor %}
            private Object active = null;
            public <T> T accept(Visitor<T> visitor) {
                {%- for _, variant_type, _ in variants %}
                if (active instanceof {{ variant_type }}) { return visitor.visit(({{ variant_type }}) active); }
                {%- endfor %}
                throw new java.lang.IllegalStateException("Illegal variant type: " + active.getClass().getName());
            }
            public void accept(VoidVisitor visitor) {
                {%- for _, variant_type, _ in variants %}
                if (active instanceof {{ variant_type }}) { visitor.visit(({{ variant_type }}) active); return; }
                {%- endfor %}
                throw new java.lang.IllegalStateException("Illegal variant type: " + active.getClass().getName());
            }
            {%- for primitive in primitives %}
            public {{ primitive }} accept({{ primitive | capitalize }}Visitor visitor) {
                {%- for _, variant_type, _ in variants %}
                if (active instanceof {{ variant_type }}) { return visitor.visit(({{ variant_type }}) active); }
                {%- endfor %}
                throw new java.lang.IllegalStateException("Illegal variant type: " + active.getClass().getName());
            }
            {%- endfor %}
            @SuppressWarnings("unchecked")
            public <T> T get(Class<T> cls) {
                if (cls.isInstance(active)) {
                    return (T) active;
                } else {
                    return null;
                }
            }
            @SuppressWarnings("unchecked")
            public <T> T set(Class<T> cls) {
            {%- for vid, variant_type, _ in variants %}
                if (cls.isInstance({{ vid }})) {
                    active = {{ vid }};
                    return (T) active;
                }
            {%- endfor %}
                throw new java.lang.IllegalStateException("Illegal variant type: " + cls.getName());
            }
            private static final {{ tag_jtype | capitalize }}Visitor tagVisitor = new {{ tag_jtype | capitalize }}Visitor() {
                {%- for _, variant_type, tag_value  in variants %}
                public {{ tag_jtype }} visit({{ variant_type }} x) {
                    return {{ tag_value }};
                }
                {%- endfor %}
            };
            {{ tag_jtype }} tag() {
                return accept(tagVisitor);
            }""",
                    locals(),
                ),
                extra,
            ]
        ),
        static=True,
    )


@dataclasses.dataclass
class BuiltVariantSizer(st.SizeVisitor[jg.Node]):
    variant: tir.Variant

    def visit_constant(self, size: st.Constant) -> jg.Node:
        return gen_raw(
            """\
            public int sizeBytes() {
                return {{ size.value }};
            }""",
            locals(),
        )

    def visit_dynamic(self, size: st.Dynamic) -> jg.Node:
        context = JavaTypeContext.get_local_variant(self.variant)
        variants = [
            (format_vartag_int(tag_value), variant_type.accept(BuiltJavaType()))
            for variant_type, tag_value in self.variant.tags.items()
        ]
        return gen_raw(
            """\
            @SuppressWarnings("unchecked")
            public int sizeBytes() {
                {%- for vid, variant_type in variants %}
                if (active instanceof {{ variant_type }}) {
                    return {{ context }}.{{ vid }}.sizeBytes(({{ variant_type }}) active);
                }
                {%- endfor %}
                throw new java.lang.IllegalStateException("Illegal variant type: " + active.getClass().getName());
            }""",
            locals(),
        )


def gen_enum(root: tir.Enum) -> jg.Node:
    class_name = BuiltJavaType.get_local_enum(root)
    builder: t.List[jg.Node] = []

    underlying = jint_type(root.underlying_type.width)
    object_underlying = object_jint(underlying)
    underlying_tako_type = root.underlying_type.accept(JavaType())
    jenum = {
        name: jint_literal(root.underlying_type.width, value)
        for name, value in root.variants.items()
    }
    ur = representable_range(root.underlying_type.width, Sign.SIGNED)

    def gen_range_check(r: Range) -> str:
        start = jint_literal(root.underlying_type.width, r.start)
        end = jint_literal(root.underlying_type.width, r.end)
        if r.is_unit():
            return f"(value == {start})"
        parts = []
        if r.start != ur.start:
            parts.append(f"value >= {start}")
        if r.end != ur.stop - 1:
            parts.append(f"value <= {end}")
        return f"({' && '.join(parts)})"

    check = " || ".join(map(gen_range_check, root.valid_ranges))
    if not check:
        check = "false"
    zero_value = jint_literal(root.underlying_type.width, 0)
    builder.append(
        gen_raw(
            """\
        {%- for name, value in jenum.items() %}
        public static final {{ class_name }} {{ name }} = new {{ class_name }}({{ value }}, true);
        {%- endfor %}
        public static final java.util.List<{{ class_name }}> VALUES = java.util.Collections.unmodifiableList(java.util.Arrays.asList({{ ", ".join(jenum.keys()) }}));
        private {{ underlying }} value;
        private final boolean isConst;
        private {{ class_name }}({{ underlying }} value, boolean isConst) {
            this.value = value;
            this.isConst = isConst;
        }
        public {{ underlying }} value() {
            return value;
        }
        public void setValue({{ underlying }} value) {
            if (isConst) {
                throw new java.lang.IllegalStateException("Cannot modify isConst enum");
            } else {
                this.value = value;
            }
        }
        public java.lang.String name() {
            {%- for name, value in jenum.items() %}
            if (value == {{ value }}) { return "{{ name }}"; }
            {%- endfor %}
            throw new java.lang.IllegalStateException("Illegal enum value: " + value);
        }
        public boolean valid() {
            return {{ check }};
        }
        public static {{ class_name }} makeUnsafe({{ underlying }} value) {
            return new {{ class_name }}(value, false);
        }
        public static {{ class_name }} makeUninitialized() {
            return new {{ class_name }}({{ zero_value }}, false);
        }
        public static {{ class_name }} valueOf({{ underlying }} value) {
            {%- for name, value in jenum.items() %}
            if (value == {{ value }}) { return {{ name }}; }
            {%- endfor %}
            return null;
        }
        public void render({{ byte_buffer }} buf, int offset) {
            setValue({{ underlying_tako_type }}.render(buf, offset));
        }
        public int parse({{ byte_buffer }} buf, int offset) throws {{ parse_exception }} {
            int endOffset = {{ underlying_tako_type }}.parse(buf, offset);
            render(buf, offset);
            if (!valid()) {
                throw new {{ parse_exception }}.Malformed();
            } else {
                return endOffset;
            }
        }
        public int serializeInto({{ byte_buffer }} buf, int offset) {
            return {{ underlying_tako_type }}.serializeInto(value, buf, offset);
        }
        public void cloneInto({{ class_name }} src) {
            setValue(src.value);
        }
        @Override
        public boolean equals(Object _other) {
            if (_other == null || ! (_other instanceof {{ class_name }})) {
                return false;
            }
            return value == (({{ class_name }}) _other).value;
        }
        @Override
        public int hashCode() {
            return java.lang.{{ object_underlying }}.hashCode(value);
        }""",
            locals(),
        )
    )

    return jg.Class(name=class_name, body=jg.Section(builder), static=True)


def gen_enum_type_class(enum: tir.Enum) -> jg.Node:
    class_name = JavaType.get_local_enum(enum)
    view_class = RenderedJavaType.get_local_enum(enum)
    built_class = BuiltJavaType.get_local_enum(enum)
    return gen_raw(
        """\
        public static class {{ class_name }} implements {{ tako_pkg }}.FixedSizeTakoType<{{ view_class }}, {{ built_class }}>{
            public {{ view_class }} newRendered() {
                return {{ view_class }}.makeUninitialized();
            }
            public {{ built_class }} newBuilt() {
                return {{ view_class }}.makeUninitialized();
            }
            public void render({{ view_class }} out, {{ byte_buffer }} buf, int offset) {
                out.render(buf, offset);
            }
            public int parse({{ view_class }} out, {{ byte_buffer }} buf, int offset) throws {{ parse_exception }} {
                return out.parse(buf, offset);
            }
            public void build({{ built_class }} out, {{ view_class }} rendered) {
                out.setValue(rendered.value());
            }
            public int serializeInto({{ built_class }} built, {{ byte_buffer }} buf, int offset) {
                return built.serializeInto(buf, offset);
            }
            public int sizeBytes({{ built_class }} built) {
                return {{ enum.size.value }};
            }
            public int sizeBytes() {
                return {{ enum.size.value }};
            }
            public void cloneInto({{ built_class }} out, {{ built_class }} src) {
                out.cloneInto(src);
            }
        }""",
        locals(),
    )


def get_built_conversion_types(conversion: cir.Conversion) -> t.Tuple[str, str, str]:
    src, target = (
        conversion.src.accept(BuiltJavaType()),
        conversion.target.accept(BuiltJavaType()),
    )
    if conversion.strength < cir.ConversionStrength.TOTAL:
        ret = f"throws {conversion_exception} "
    else:
        ret = ""
    return src, target, ret


@dataclasses.dataclass
class BuiltConversionGenerator(cir.RootConversionVisitor[jg.Node]):
    def visit_enum_conversion(self, conversion: cir.EnumConversion) -> jg.Node:
        src_jtype, target_jtype, return_jtype = get_built_conversion_types(conversion)

        return gen_raw(
            """\
            public static void convert({{ target_jtype }} out, {{ src_jtype }} src) {{ return_jtype }}{
                {%- for evm in conversion.mapping %}
                if (src.equals({{ src_jtype }}.{{ evm.src.name }})) {
                    {%- if evm.target is none %}
                    throw new {{ tako_pkg }}.ConversionException();
                    {%- else %}
                    out.cloneInto({{ target_jtype }}.{{ evm.target.name }});
                    return;
                    {%- endif %}
                }
                {%- endfor %}
                throw new java.lang.IllegalStateException("Illegal enum value: " + src);
            }""",
            locals(),
        )

    def visit_struct_conversion(self, conversion: cir.StructConversion) -> jg.Node:
        context = JavaTypeContext.get_local_struct(conversion.target)
        src_jtype, target_jtype, return_jtype = get_built_conversion_types(conversion)

        conversion_stmts: t.List[t.Tuple[str, str, str]] = []
        for fname, field in conversion.target.get_owned():
            conversion_stmts.append(
                (
                    fname,
                    field.type_.accept(BuiltJavaType()),
                    conversion.mapping[fname].accept(
                        BuiltConversionExpressionGenerator(
                            f"{context}.{fname}",
                            f"out.{snake_to_camel(fname)}()",
                            f"out.{snake_to_camel('set_' + fname)}",
                            "src",
                        )
                    ),
                )
            )

        return gen_raw(
            """\
            public static void convert({{ target_jtype }} out, {{ src_jtype }} src) {{ return_jtype }}{
                {%-for field_name, field_jtype, conversion_stmt  in conversion_stmts %}
                {{ conversion_stmt }};
                {%-endfor %}
            }""",
            locals(),
        )

    def visit_variant_conversion(self, conversion: cir.VariantConversion) -> jg.Node:
        context = JavaTypeContext.get_local_variant(conversion.target)
        src_jtype, target_jtype, return_jtype = get_built_conversion_types(conversion)

        visitors = []
        for vvm in conversion.mapping:
            variant_jtype = vvm.src.type_.accept(BuiltJavaType())
            if vvm.target is None:
                conversion_expr = None
                converted_jtype = None
            else:
                converted_jtype = vvm.target.target.type_.accept(BuiltJavaType())
                conversion_expr = vvm.target.conversion.accept(
                    BuiltConversionExpressionGenerator(
                        f"{context}.{format_vartag_int(vvm.target.target.value)}",
                        f"out.set({converted_jtype}.class)",
                        "",
                        "current",
                    )
                )
            visitors.append((variant_jtype, conversion_expr, converted_jtype))

        return gen_raw(
            """\
            public static void convert({{ target_jtype }} out, {{ src_jtype }} src) {{ return_jtype }}{
                {%- for variant_jtype, conversion_stmt, converted_jtype in visitors %}
                {
                    {{ variant_jtype }} current = src.get({{ variant_jtype }}.class);
                    if (current != null) {
                        {%- if conversion_stmt is none %}
                        throw new {{ tako_pkg }}.ConversionException();
                        {%- else %}
                        {{ conversion_stmt }};
                        return;
                        {%- endif %}
                    }
                }
                {%- endfor %}
                throw new java.lang.IllegalStateException("Illegal src variant");
            }""",
            locals(),
        )


@dataclasses.dataclass
class BuiltConversionExpressionGenerator(
    cir.ConversionVisitor[str], cir.FieldConversionVisitor[str]
):
    tako_type_expr: str
    out_loc: str
    out_loc_setter: str
    src_expr: str

    def visit_identity_conversion(self, conversion: cir.IdentityConversion) -> str:
        if is_jprimitive(conversion.src):
            return f"{self.out_loc_setter}({self.src_expr});"
        else:
            return f"{self.tako_type_expr}.cloneInto({self.out_loc}, {self.src_expr});"

    def root_conversion_expr(self, conversion: cir.RootConversion) -> str:
        fname = qname_to_cpp(conversion.protocol.with_name("convert"))
        return f"{fname}({self.out_loc}, {self.src_expr});"

    def visit_enum_conversion(self, conversion: cir.EnumConversion) -> str:
        return self.root_conversion_expr(conversion)

    def visit_struct_conversion(self, conversion: cir.StructConversion) -> str:
        return self.root_conversion_expr(conversion)

    def visit_int_default_field_conversion(
        self, conversion: cir.IntDefaultFieldConversion
    ) -> str:
        value = jint_literal(conversion.type_.width, conversion.value)
        return f"{self.out_loc_setter}({value});"

    def visit_enum_default_field_conversion(
        self, conversion: cir.EnumDefaultFieldConversion
    ) -> str:
        jtype = conversion.type_.accept(BuiltJavaType())
        return f"{self.out_loc}.cloneInto({jtype}.{conversion.value.name});"

    def visit_transform_field_conversion(
        self, conversion: cir.TransformFieldConversion
    ) -> str:
        inner_src_expr = f"{self.src_expr}.{snake_to_camel(conversion.src_field)}()"
        return conversion.conversion.accept(
            BuiltConversionExpressionGenerator(
                self.tako_type_expr, self.out_loc, self.out_loc_setter, inner_src_expr
            )
        )

    def visit_variant_conversion(self, conversion: cir.VariantConversion) -> str:
        return self.root_conversion_expr(conversion)


@dataclasses.dataclass
class ViewConversionGenerator(cir.ConversionVisitor[t.Optional[jg.Node]]):
    def visit_identity_conversion(self, conversion: cir.IdentityConversion) -> jg.Node:
        raise InternalError()

    def visit_enum_conversion(
        self, conversion: cir.EnumConversion
    ) -> t.Optional[jg.Node]:
        # There are no enum views, don't need to generate anything
        return None

    def visit_struct_conversion(
        self, conversion: cir.StructConversion
    ) -> t.Optional[jg.Node]:
        # If the conversion is compatible, generate a conversion between the view types
        # Otherwise emit nothing
        if conversion.strength < cir.ConversionStrength.COMPATIBLE:
            return None

        src_jtype = conversion.src.accept(RenderedJavaType())
        target_jtype = conversion.target.accept(RenderedJavaType())

        # You take the buffer under the old type, and parse it as the new type.
        # You need to parse it again to resolve any-variable length fields.
        # But this will do more bounds checks then needed.
        return gen_raw(
            """\
            public static void convert({{ target_jtype }} out, {{ src_jtype }} src) {
                out.render(src.backingBuffer(), src.backingBufferOffset());
            }""",
            locals(),
        )

    def visit_variant_conversion(
        self, conversion: cir.VariantConversion
    ) -> t.Optional[jg.Node]:
        # TODO: this is annoying, but would be nice
        return None


def jint_type(width: int) -> str:
    if width == 1:
        return "byte"
    elif width == 2:
        return "short"
    elif width == 4:
        return "int"
    elif width == 8:
        return "long"
    else:
        raise ValueError(f"No java type for width: {width}")


def jfloat_type(width: int) -> str:
    if width == 4:
        return "float"
    elif width == 8:
        return "double"
    else:
        raise ValueError(f"No java type for width: {width}")


def object_jint(primitive: str) -> str:
    if primitive == "byte":
        return "Byte"
    if primitive == "short":
        return "Short"
    if primitive == "int":
        return "Integer"
    if primitive == "long":
        return "Long"
    raise ValueError()


def jint_literal(width: int, value: int) -> str:
    # If the value is not within the range of a signed type
    # of the target width, that means it has the high bit set
    # Subtract 2 * the most negative signed number.
    # Example: width = 3 bits.
    # Then r = [-4, 3] (the range of a signed number), but
    # an unsigned 3 bit number can be in [0, 7].
    # If value is >= 4, subtract 8. This works:
    # 4 => -4 (0b100 => 0b100)
    # 5 => -3 (0b101 => 0b101)
    # 6 => -2 (0b110 => 0b110)
    # 7 => -1 (0b111 => 0b111)
    r = representable_range(width, Sign.SIGNED)
    if value not in r:
        # Note that r.start is negative!
        value += 2 * r.start
    jtype = jint_type(width)
    suffix = ""
    # If this type is long, use the L suffix to permit a large
    # literal
    if width == 8:
        suffix = "L"
    # Cast to the correct type because in Java an integer literal
    # can only be an int or a long, so to get a smaller literal
    # we cast.
    return f"(({jtype}){value}{suffix})"


def cpp_offset_expr(
    offset: st.Offset, base_offset: str, field_offset_prefix: str
) -> str:
    if offset.base is None:
        offset_base = base_offset
    else:
        offset_base = f"{field_offset_prefix}{offset.base}"
    return f"{offset_base} + {offset.offset}"


def endianness_to_java(e: Endianness) -> str:
    if e == Endianness.BIG:
        return "b"
    else:
        return "l"


def to_namespace(parts: t.Iterable[str]) -> str:
    return ".".join(parts)


def qname_to_cpp(qname: QName) -> str:
    return to_namespace(qname.parts)


def primitive_tako_type(type_class: str, width: int, endianness: Endianness) -> str:
    return f"{tako_pkg}.Primitives.{type_class}{width}{endianness_to_java(endianness).capitalize()}"


def is_jprimitive(type_: tir.Type) -> bool:
    return isinstance(type_, tir.Int) or isinstance(type_, tir.Float)


@dataclasses.dataclass
class JavaType(tir.TypeVisitor[str]):
    @staticmethod
    def get_local_struct(type_: tir.Struct) -> str:
        return f"{type_.name.name()}TakoType"

    @staticmethod
    def get_local_enum(type_: tir.Enum) -> str:
        return f"{type_.name.name()}TakoType"

    @staticmethod
    def get_local_variant(type_: tir.Variant) -> str:
        return f"{type_.name.name()}TakoType"

    def visit_int(self, type_: tir.Int) -> str:
        return primitive_tako_type("Integer", type_.width, type_.endianness)

    def visit_float(self, type_: tir.Float) -> str:
        return primitive_tako_type("Float", type_.width, type_.endianness)

    def visit_array(self, type_: tir.Array) -> str:
        return self.handle_seq(type_.inner, "Array")

    def visit_vector(self, type_: tir.Vector) -> str:
        return self.handle_seq(type_.inner, "Vector")

    def visit_list(self, type_: tir.List) -> str:
        # Note that a list will never have an Int or Enum
        # as the inner type
        return self.handle_seq(type_.inner, "List")

    def handle_seq(self, inner: tir.Type, seq_type: str) -> str:
        if is_jprimitive(inner):
            return f"{inner.accept(JavaType())}.{seq_type}TakoType"
        else:
            return f"{tako_pkg}.{seq_type}TakoType<{inner.accept(RenderedJavaType())}, {inner.accept(BuiltJavaType())}, {inner.accept(JavaType())}>"

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> str:
        return type_.variant.accept(self)

    def visit_virtual(self, type_: tir.Virtual) -> str:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> str:
        return self.namespace(root, JavaType.get_local_struct(root))

    def visit_variant(self, root: tir.Variant) -> str:
        return self.namespace(root, JavaType.get_local_variant(root))

    def visit_enum(self, root: tir.Enum) -> str:
        return self.namespace(root, JavaType.get_local_enum(root))

    def namespace(self, type_: tir.RootType, local_name: str) -> str:
        return qname_to_cpp(type_.name.namespace().with_name(local_name))


@dataclasses.dataclass
class JavaTypeInstance(tir.TypeVisitor[str]):
    def visit_int(self, type_: tir.Int) -> str:
        return self.handle_common(type_)

    def visit_float(self, type_: tir.Float) -> str:
        return self.handle_common(type_)

    def visit_array(self, type_: tir.Array) -> str:
        return self.handle_seq(type_, type_.inner, str(type_.length))

    def visit_vector(self, type_: tir.Vector) -> str:
        return self.handle_seq(type_, type_.inner, None)

    def visit_list(self, type_: tir.List) -> str:
        return self.handle_seq(type_, type_.inner, None)

    def handle_seq(
        self, type_: tir.Type, inner: tir.Type, extra_arg: t.Optional[str]
    ) -> str:
        args: t.List[str]
        if is_jprimitive(inner):
            args = []
        else:
            args = [inner.accept(self)]
        if extra_arg is not None:
            args.append(extra_arg)
        return f"new {type_.accept(JavaType())}({', '.join(args)})"

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> str:
        return type_.variant.accept(self)

    def visit_virtual(self, type_: tir.Virtual) -> str:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> str:
        return self.handle_common(root)

    def visit_variant(self, root: tir.Variant) -> str:
        return self.handle_common(root)

    def visit_enum(self, root: tir.Enum) -> str:
        return self.handle_common(root)

    def handle_common(self, type_: tir.Type) -> str:
        return f"new {type_.accept(JavaType())}()"


@dataclasses.dataclass
class RenderedJavaType(tir.TypeVisitor[str]):
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
        return jint_type(type_.width)

    def visit_float(self, type_: tir.Float) -> str:
        return jfloat_type(type_.width)

    def visit_array(self, type_: tir.Array) -> str:
        return self.handle_seq(type_.inner, "Array")

    def visit_vector(self, type_: tir.Vector) -> str:
        return self.handle_seq(type_.inner, "Vector")

    def visit_list(self, type_: tir.List) -> str:
        return self.handle_seq(type_.inner, "List")

    def handle_seq(self, inner: tir.Type, seq_type: str) -> str:
        if is_jprimitive(inner):
            return f"{inner.accept(JavaType())}.{seq_type}View"
        else:
            return f"{tako_pkg}.{seq_type}View<{inner.accept(RenderedJavaType())}, {inner.accept(BuiltJavaType())}, {inner.accept(JavaType())}>"

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> str:
        return type_.variant.accept(self)

    def visit_virtual(self, type_: tir.Virtual) -> str:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> str:
        return self.namespace(root, RenderedJavaType.get_local_struct(root))

    def visit_variant(self, root: tir.Variant) -> str:
        return self.namespace(root, RenderedJavaType.get_local_variant(root))

    def visit_enum(self, root: tir.Enum) -> str:
        return self.namespace(root, RenderedJavaType.get_local_enum(root))

    def namespace(self, type_: tir.RootType, local_name: str) -> str:
        return qname_to_cpp(type_.name.namespace().with_name(local_name))


@dataclasses.dataclass
class BuiltJavaType(tir.TypeVisitor[str]):
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
        return jint_type(type_.width)

    def visit_float(self, type_: tir.Float) -> str:
        return jfloat_type(type_.width)

    def visit_array(self, type_: tir.Array) -> str:
        return self.handle_seq(type_.inner, "Array")

    def visit_vector(self, type_: tir.Vector) -> str:
        return self.handle_seq(type_.inner, "Vector")

    def visit_list(self, type_: tir.List) -> str:
        return self.handle_seq(type_.inner, "List")

    def handle_seq(self, inner: tir.Type, seq_type: str) -> str:
        if is_jprimitive(inner):
            return f"{fastutil}.{inner.accept(BuiltJavaType())}s.{inner.accept(BuiltJavaType()).capitalize()}ArrayList"
        else:
            return f"{arraylist}<{inner.accept(self)}>"

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> str:
        return type_.variant.accept(self)

    def visit_virtual(self, type_: tir.Virtual) -> str:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> str:
        return self.namespace(root, BuiltJavaType.get_local_struct(root))

    def visit_variant(self, root: tir.Variant) -> str:
        return self.namespace(root, BuiltJavaType.get_local_variant(root))

    def visit_enum(self, root: tir.Enum) -> str:
        return self.namespace(root, BuiltJavaType.get_local_enum(root))

    def namespace(self, type_: tir.RootType, local_name: str) -> str:
        return qname_to_cpp(type_.name.namespace().with_name(local_name))


class JavaTypeContext:
    @staticmethod
    def get_local_struct(type_: tir.Struct) -> str:
        return f"{type_.name.name()}TakoContext"

    @staticmethod
    def get_struct(root: tir.Struct) -> str:
        return qname_to_cpp(
            root.name.namespace().with_name(JavaTypeContext.get_local_struct(root))
        )

    @staticmethod
    def get_local_variant(type_: tir.Variant) -> str:
        return f"{type_.name.name()}TakoContext"

    @staticmethod
    def get_variant(root: tir.Variant) -> str:
        return qname_to_cpp(
            root.name.namespace().with_name(JavaTypeContext.get_local_variant(root))
        )


def gen_raw(template: str, env: t.Dict[str, t.Any]) -> jg.Raw:
    return jg.Raw(template_raw(template, {**globals(), **env}))
