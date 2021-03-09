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

import typing as t
import dataclasses
import argparse
import json
from pathlib import Path
from tako.util.qname import QName
from tako.core.sir import Protocol, tir, kir, cir
from tako.generators.generator import Generator
from tako.util.pretty_printer import PrettyPrinter
from tako.generators.python import python_gen as pg
from tako.generators.template import template_raw
from tako.util.name_format import pascal_to_snake
from tako.util.cast import checked_cast, unwrap, assert_never
from tako.core.internal_error import InternalError
import tako.core.size_types as st
from tako.util.int_model import Sign, Endianness

parse_error = "tako.runtime.ParseError"


class PythonGenerator(Generator):
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def generate_into(self, proto: Protocol, out_dir: Path, args: t.Any) -> None:
        # Helps mypy -- doing one big list concat doesn't work
        sections: t.List[pg.Node] = []
        sections += [
            pg.Raw(
                """\
            # flake8: noqa

            import typing
            import abc
            import struct
            import dataclasses
            import enum

            import tako.runtime"""
            )
        ]
        sections += [
            pg.Raw(f"import {python_module(ext)}")
            for ext in proto.types.external_protocols
        ]
        sections += [
            constant.accept(RootConstantGenerator())
            for constant in proto.constants.constants.values()
        ]
        sections += [
            proto.types.types[name].accept_rtv(RootTypeGenerator())
            for name in proto.types.own
        ]
        sections += [
            proto.types.types[name].accept_rtv(RootMarkerTypeGenerator())
            for name in proto.types.own
        ]
        sections += gen_conversions(proto.name, proto.conversions.own)

        base_name = python_relative_path(proto.name)
        proto_file = out_dir / base_name
        proto_file.parent.mkdir(parents=True, exist_ok=True)
        with proto_file.open("w") as out:
            generated = pg.Section(sections)
            printer = PrettyPrinter(4, out)
            generated.pretty_printer(printer)

        base_dir = base_name.parent
        while len(base_dir.parts) != 0:
            dr = out_dir / base_dir
            with (out_dir / base_dir / "__init__.py").open("w"):
                pass
            base_dir = base_dir.parent

    def list_outputs(
        self, proto_qname: QName, args: t.Any
    ) -> t.Generator[Path, None, None]:
        return
        yield


def python_module(qname: QName) -> QName:
    proto_name = qname.name()
    return qname.namespace().with_name(proto_name)


def python_relative_path(qname: QName) -> Path:
    qname = python_module(qname)
    proto_name = qname.name()
    proto_namespace = qname.namespace()
    return Path(*proto_namespace.parts) / Path(f"{proto_name}.py")


@dataclasses.dataclass
class RootTypeGenerator(tir.RootTypeVisitor[pg.Node]):
    def visit_struct(self, root: tir.Struct) -> pg.Node:
        class_name = get_local_struct(root)
        pyfields = [
            (fname, field.type_.accept(PythonType(root.name.namespace())))
            for fname, field in root.get_owned()
        ]

        return pg.Class(
            class_name,
            pg.Section(
                [
                    pg.Section(
                        [pg.Raw(f"{fname}: {pytype}") for fname, pytype in pyfields]
                    ),
                    gen_parser(root),
                    gen_serializer(root),
                    gen_sizer(root),
                ]
            ),
            decorator="@dataclasses.dataclass(frozen=True)",
        )

    def visit_variant(self, root: tir.Variant) -> pg.Node:
        class_name = get_local_variant(root)
        visitor_name = get_visitor_name(root, root.name.namespace())
        type_var_name = f"{class_name}TypeVar"

        visitor_info = [
            (
                root.tags[variant],
                vname,
                variant.accept(PythonType(root.name.namespace())),
            )
            for variant, vname in get_visitor_info(root).items()
        ]
        variant_type_list = ", ".join([vtype for _, _, vtype in visitor_info])
        tag_pytype = root.tag_type.accept(PythonType(root.name.namespace()))

        return gen_raw(
            """\
        {{ type_var_name }} = typing.TypeVar("{{ type_var_name }}")
        class {{ visitor_name }}(abc.ABC, typing.Generic[{{ type_var_name }}]):
            {%- for tag_value, vname, vtype in visitor_info %}
            @abc.abstractmethod
            def {{ vname }}(self, value: {{ vtype }}) -> {{ type_var_name }}:
                ...
            {%- endfor %}
        @dataclasses.dataclass
        class {{ class_name }}:
            value: typing.Union[{{ variant_type_list }}]
            types: typing.ClassVar[typing.List[typing.Type]] = [{{ variant_type_list }}]
            def accept(self, visitor: {{ visitor_name }}[{{ type_var_name }}]) -> {{ type_var_name }}:
                {%- for tag_value, vname, vtype in visitor_info %}
                if isinstance(self.value, {{ vtype }}):
                    return visitor.{{ vname }}(self.value)
                    return
                {%- endfor %}
                raise ValueError('Variant held illegal type')
            def tag(self) -> {{ tag_pytype }}:
                {%- for tag_value, vname, vtype in visitor_info %}
                if isinstance(self.value, {{ vtype }}):
                    return {{ tag_value }}
                {%- endfor %}
                raise ValueError('Variant held illegal type')
            @staticmethod
            def parse(buf: bytes, offset: int, tag: {{ tag_pytype }}) -> typing.Union[{{ parse_error }}, typing.Tuple[int, '{{ class_name }}']]:
                value: typing.Union[{{ variant_type_list }}]
                {%- for tag_value, vname, vtype in visitor_info %}
                if tag == {{ tag_value }}:
                    value_inner_{{ loop.index0 }} = {{ vtype }}.parse(buf, offset)
                    if isinstance(value_inner_{{ loop.index0 }}, {{ parse_error }}):
                        return value_inner_{{ loop.index0 }}
                    offset, value = value_inner_{{ loop.index0 }}
                    return offset, {{ class_name }}(value)
                {%- endfor %}
                return {{ parse_error }}.MALFORMED
            def serialize_into(self, buf: bytearray, offset: int) -> int:
                return self.value.serialize_into(buf, offset)
            def serialize(self) -> bytearray:
                return self.value.serialize()
            def size_bytes(self) -> int:
                return self.value.size_bytes()""",
            locals(),
        )

    def visit_enum(self, root: tir.Enum) -> pg.Node:
        class_name = get_local_enum(root)
        return gen_raw(
            """\
        @enum.unique
        class {{ class_name }}(enum.Enum):
            {%- for name, value in root.variants.items() %}
            {{ name }} = {{ value }}
            {%- endfor %}
            @staticmethod
            def from_int(value: int) -> typing.Union[{{ parse_error }}, '{{ class_name }}']:
                try:
                    return {{ class_name }}(value)
                except ValueError:
                    return {{ parse_error }}.MALFORMED""",
            locals(),
        )


def gen_parser(struct: tir.Struct) -> pg.Node:
    class_name = get_local_struct(struct)

    parser_parts: t.List[pg.Node] = []
    helpers: t.List[pg.Node] = []
    parser_parts.append(
        gen_raw(
            """\
        _ctxt: typing.Dict[str, typing.Any] = {}
    """,
            locals(),
        )
    )
    for fname, field in struct.fields.items():
        pname, fhelpers = field.type_.accept(
            FieldParserGenerator(struct.name.namespace(), class_name, fname)
        )
        helpers.append(fhelpers)
        # If the field is virtual expose the parsing function
        if isinstance(field.type_, tir.Virtual):
            pytype = field.type_.accept(PythonType(struct.name.namespace()))
            # self.__dict__ is the context -- the struct itself is the context
            helpers.append(
                gen_raw(
                    """\
                def {{ fname }}(self, buf: bytes, offset: int) -> typing.Union[{{ parse_error }}, typing.Tuple[int, {{ pytype }}]]:
                    return {{ class_name }}.{{ pname }}(buf, offset, self.__dict__)""",
                    locals(),
                )
            )
        else:
            # If the field is a dependent field, parse it, but store the value in the
            # context dictionary -- the class itself doesn't store it
            if field.master_field is not None:
                dst_expr = f'_ctxt["{fname}"]'
            else:
                dst_expr = fname
            parser_parts.append(
                gen_raw(
                    """\
                _{{ fname }}_inner = {{ class_name }}.{{ pname }}(_buf, _offset, _ctxt)
                if isinstance(_{{ fname }}_inner, {{ parse_error }}):
                    return _{{ fname }}_inner
                _offset, {{ dst_expr }} = _{{ fname }}_inner""",
                    locals(),
                )
            )

    owned = [owned_fname for owned_fname, _ in struct.get_owned()]
    parser_parts.append(
        gen_raw(
            """\
        return _offset, {{ class_name }}({{ owned|join(', ') }})""",
            locals(),
        )
    )

    helpers.append(
        pg.Function(
            "parse",
            [(pg.Type("bytes"), "_buf"), (pg.Type("int"), "_offset")],
            pg.Type(
                f"typing.Union[{ parse_error }, typing.Tuple[int, '{class_name}']]"
            ),
            pg.Section(parser_parts),
            decorator="@staticmethod",
        )
    )

    return pg.Section(helpers)


@dataclasses.dataclass
class FieldParserGenerator(
    tir.TypeVisitor[t.Tuple[str, pg.Node]], tir.LengthVisitor[str]
):
    current_proto: QName
    class_name: str
    fname: str
    num: int = 0

    def visit_int(self, type_: tir.Int) -> t.Tuple[str, pg.Node]:
        return self.handle_int_like(type_, int_struct_pack_format(type_))

    def visit_float(self, type_: tir.Float) -> t.Tuple[str, pg.Node]:
        return self.handle_int_like(type_, float_struct_pack_format(type_))

    def visit_array(self, type_: tir.Array) -> t.Tuple[str, pg.Node]:
        return self.handle_seq(
            type_, type_.inner, self.handle_fixed_length(type_.length)
        )

    def visit_vector(self, type_: tir.Vector) -> t.Tuple[str, pg.Node]:
        return self.handle_seq(
            type_, type_.inner, self.handle_field_reference(type_.length)
        )

    def visit_list(self, type_: tir.List) -> t.Tuple[str, pg.Node]:
        return self.handle_seq(type_, type_.inner, type_.length.accept(self))

    def visit_detached_variant(
        self, type_: tir.DetachedVariant
    ) -> t.Tuple[str, pg.Node]:
        pytype = type_.accept(PythonType(self.current_proto))
        pname = self.alloc_parse_function()
        tag_expr = self.handle_field_reference(type_.tag)

        return (
            pname,
            gen_raw(
                """\
            @staticmethod
            def {{ pname }}(buf: bytes, offset: int, ctxt: typing.Dict[str, typing.Any]) -> typing.Union[{{ parse_error }}, typing.Tuple[int, {{ pytype }}]]:
                return {{ pytype }}.parse(buf, offset, {{ tag_expr }})""",
                locals(),
            ),
        )

    def visit_virtual(self, type_: tir.Virtual) -> t.Tuple[str, pg.Node]:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> t.Tuple[str, pg.Node]:
        pytype = root.accept(PythonType(self.current_proto))
        pname = self.alloc_parse_function()
        return (
            pname,
            gen_raw(
                """\
            @staticmethod
            def {{ pname }}(buf: bytes, offset: int, ctxt: typing.Dict[str, typing.Any]) -> typing.Union[{{ parse_error }}, typing.Tuple[int, {{ pytype }}]]:
                return {{ pytype }}.parse(buf, offset)""",
                locals(),
            ),
        )

    def visit_variant(self, root: tir.Variant) -> t.Tuple[str, pg.Node]:
        raise InternalError()

    def visit_enum(self, root: tir.Enum) -> t.Tuple[str, pg.Node]:
        pytype = root.accept(PythonType(self.current_proto))
        return self.handle_int_like(
            root,
            int_struct_pack_format(root.underlying_type),
            conversion_func=f"{pytype}.from_int",
        )

    def alloc_parse_function(self) -> str:
        result = f"_parse_{self.fname}{self.num}"
        self.num += 1
        return result

    def handle_fixed_length(self, length: int) -> str:
        return str(length)

    def handle_field_reference(self, fr: tir.FieldReference) -> str:
        return f"ctxt['{fr.name}']"

    def visit_fixed_length(self, length: tir.FixedLength) -> str:
        return self.handle_fixed_length(length.length)

    def visit_variable_length(self, length: tir.VariableLength) -> str:
        return self.handle_field_reference(length.length)

    def handle_int_like(
        self, type_: tir.Type, pack_expr: str, conversion_func: t.Optional[str] = None
    ) -> t.Tuple[str, pg.Node]:
        pname = self.alloc_parse_function()
        pytype = type_.accept(PythonType(self.current_proto))
        size = checked_cast(st.Constant, type_.size).value

        return (
            pname,
            gen_raw(
                """\
            @staticmethod
            def {{ pname }}(buf: bytes, offset: int, ctxt: typing.Dict[str, typing.Any]) -> typing.Union[{{ parse_error }}, typing.Tuple[int, {{ pytype }}]]:
                end = offset + {{ size }}
                if end > len(buf):
                    return {{ parse_error }}.NOT_ENOUGH_DATA
                value = struct.unpack('{{ pack_expr }}', buf[offset:end])[0]
                {%- if conversion_func is none %}
                return offset + {{ size }}, value
                {%- else %}
                converted_value = {{ conversion_func }}(value)
                if isinstance(converted_value, {{ parse_error }}):
                    return converted_value
                return offset + {{ size }}, converted_value
                {%- endif %}
                """,
                locals(),
            ),
        )

    def handle_seq(
        self, seq: tir.Type, inner: tir.Type, length_expr: str
    ) -> t.Tuple[str, pg.Node]:
        pname = self.alloc_parse_function()
        inner_pname, inner_helpers = inner.accept(self)

        pytype = seq.accept(PythonType(self.current_proto))
        inner_pytype = inner.accept(PythonType(self.current_proto))

        return (
            pname,
            pg.Section(
                [
                    inner_helpers,
                    gen_raw(
                        """\
                    @staticmethod
                    def {{ pname }}(buf: bytes, offset: int, ctxt: typing.Dict[str, typing.Any]) -> typing.Union[{{ parse_error }}, typing.Tuple[int, {{ pytype }}]]:
                        result: typing.List[{{ inner_pytype }}] = []
                        for i in range({{ length_expr }}):
                            inner_result = {{ this.class_name }}.{{ inner_pname }}(buf, offset, ctxt)
                            if isinstance(inner_result, {{ parse_error }}):
                                return inner_result
                            else:
                                offset, value = inner_result
                                result.append(value)
                        return offset, result""",
                        locals(),
                    ),
                ]
            ),
        )


def gen_serializer(struct: tir.Struct) -> pg.Node:
    class_name = get_local_struct(struct)

    builder_parts: t.List[pg.Node] = []
    helpers: t.List[pg.Node] = []
    for fname, field in struct.get_non_virtual():
        bname, fhelpers = field.type_.accept(
            FieldSerializerGenerator(struct.name.namespace(), class_name, fname)
        )
        helpers.append(fhelpers)
        # If the field is a dependent field, generate its value from some other field
        if field.master_field is not None:
            if field.master_field.key_property == tir.KeyProperty.VARIANT_TAG:
                fvalue_expr = f"self.{field.master_field.master_field}.tag()"
            elif field.master_field.key_property == tir.KeyProperty.SEQ_LENGTH:
                fvalue_expr = f"len(self.{field.master_field.master_field})"
            else:
                assert_never(field.master_field.key_property)
        else:
            fvalue_expr = f"self.{fname}"
        builder_parts.append(
            pg.Raw(f"offset = self.{bname}({fvalue_expr}, buf, offset)")
        )
    builder_parts.append(pg.Raw("return offset"))

    helpers.append(
        pg.Function(
            "serialize_into",
            [(None, "self"), (pg.Type("bytearray"), "buf"), (pg.Type("int"), "offset")],
            pg.Type("int"),
            pg.Section(builder_parts),
        )
    )

    helpers.append(
        gen_raw(
            """\
        def serialize(self) -> bytearray:
            result = bytearray(self.size_bytes())
            self.serialize_into(result, 0)
            return result""",
            locals(),
        )
    )

    return pg.Section(helpers)


@dataclasses.dataclass
class FieldSerializerGenerator(
    tir.TypeVisitor[t.Tuple[str, pg.Node]], tir.LengthVisitor[t.Optional[int]]
):
    current_proto: QName
    class_name: str
    fname: str
    num: int = 0

    def visit_int(self, type_: tir.Int) -> t.Tuple[str, pg.Node]:
        return self.handle_int_like(type_, int_struct_pack_format(type_))

    def visit_float(self, type_: tir.Float) -> t.Tuple[str, pg.Node]:
        return self.handle_int_like(type_, float_struct_pack_format(type_))

    def visit_array(self, type_: tir.Array) -> t.Tuple[str, pg.Node]:
        return self.handle_seq(type_, type_.inner, type_.length)

    def visit_vector(self, type_: tir.Vector) -> t.Tuple[str, pg.Node]:
        return self.handle_seq(type_, type_.inner, None)

    def visit_list(self, type_: tir.List) -> t.Tuple[str, pg.Node]:
        return self.handle_seq(type_, type_.inner, type_.length.accept(self))

    def visit_detached_variant(
        self, type_: tir.DetachedVariant
    ) -> t.Tuple[str, pg.Node]:
        return self.handle_root(type_)

    def visit_virtual(self, type_: tir.Virtual) -> t.Tuple[str, pg.Node]:
        raise InternalError()

    def visit_struct(self, root: tir.Struct) -> t.Tuple[str, pg.Node]:
        return self.handle_root(root)

    def visit_variant(self, root: tir.Variant) -> t.Tuple[str, pg.Node]:
        raise InternalError()

    def visit_enum(self, root: tir.Enum) -> t.Tuple[str, pg.Node]:
        return self.handle_int_like(
            root,
            int_struct_pack_format(root.underlying_type),
            value_to_int_suffix=".value",
        )

    def alloc_build_function(self) -> str:
        result = f"_serialize_{self.fname}{self.num}"
        self.num += 1
        return result

    def handle_fixed_length(self, length: int) -> str:
        return str(length)

    def handle_field_reference(self, fr: tir.FieldReference) -> str:
        return f"ctxt['{fr.name}']"

    def visit_fixed_length(self, length: tir.FixedLength) -> t.Optional[int]:
        return length.length

    def visit_variable_length(self, length: tir.VariableLength) -> t.Optional[int]:
        return None

    def handle_int_like(
        self, type_: tir.Type, pack_expr: str, value_to_int_suffix: str = ""
    ) -> t.Tuple[str, pg.Node]:
        bname = self.alloc_build_function()
        pytype = type_.accept(PythonType(self.current_proto))
        size = checked_cast(st.Constant, type_.size).value

        return (
            bname,
            gen_raw(
                """\
            def {{ bname }}(self, value: {{ pytype }}, buf: bytearray, offset: int) -> int:
                buf[offset:offset + {{ size }}] = struct.pack('{{ pack_expr }}', value{{ value_to_int_suffix }})
                return offset + {{ size }}""",
                locals(),
            ),
        )

    def handle_seq(
        self, seq: tir.Type, inner: tir.Type, expected_length: t.Optional[int]
    ) -> t.Tuple[str, pg.Node]:
        bname = self.alloc_build_function()
        inner_bname, inner_helpers = inner.accept(self)

        pytype = seq.accept(PythonType(self.current_proto))

        length_check: t.Optional[str] = None
        if expected_length is not None:
            length_check = f"assert len(value) == {expected_length}"

        return (
            bname,
            pg.Section(
                [
                    inner_helpers,
                    gen_raw(
                        """\
            def {{ bname }}(self, value: {{ pytype }}, buf: bytearray, offset: int) -> int:
                {%- if length_check is not none %}
                {{ length_check }}
                {%- endif %}
                for x in value:
                    offset = self.{{ inner_bname }}(x, buf, offset)
                return offset""",
                        locals(),
                    ),
                ]
            ),
        )

    def handle_root(self, type_: tir.Type) -> t.Tuple[str, pg.Node]:
        bname = self.alloc_build_function()
        pytype = type_.accept(PythonType(self.current_proto))

        return (
            bname,
            gen_raw(
                """\
            def {{ bname }}(self, value: {{ pytype }}, buf: bytearray, offset: int) -> int:
                return value.serialize_into(buf, offset)""",
                locals(),
            ),
        )


def gen_sizer(struct: tir.Struct) -> pg.Node:

    sizer_parts: t.List[pg.Node] = []
    helpers: t.List[pg.Node] = []
    sizer_parts.append(pg.Raw(f"result: int = 0"))
    base_size = 0
    for fname, field in struct.get_non_virtual():
        size_info = field.type_.accept(
            FieldSizerGenerator(struct.name.namespace(), fname)
        )
        if isinstance(size_info, int):
            base_size += size_info
        elif isinstance(size_info, tuple):
            sname, fhelpers = size_info
            helpers.append(fhelpers)
            sizer_parts.append(pg.Raw(f"result += self.{sname}(self.{fname})"))
        else:
            assert_never()
    sizer_parts.append(pg.Raw(f"return result + {base_size}"))
    helpers.append(
        pg.Function(
            "size_bytes", [(None, "self")], pg.Type("int"), pg.Section(sizer_parts)
        )
    )
    return pg.Section(helpers)


@dataclasses.dataclass
class FieldSizerGenerator(tir.TypeVisitor[t.Union[int, t.Tuple[str, pg.Node]]]):
    current_proto: QName
    fname: str
    num: int = 0

    def visit_int(self, type_: tir.Int) -> t.Union[int, t.Tuple[str, pg.Node]]:
        return self.handle_fixed_size(type_)

    def visit_float(self, type_: tir.Float) -> t.Union[int, t.Tuple[str, pg.Node]]:
        return self.handle_fixed_size(type_)

    def visit_array(self, type_: tir.Array) -> t.Union[int, t.Tuple[str, pg.Node]]:
        return self.handle_fixed_size(type_)

    def visit_vector(self, type_: tir.Vector) -> t.Union[int, t.Tuple[str, pg.Node]]:
        sname = self.alloc_size_function()
        inner_size = checked_cast(int, type_.inner.accept(self))
        pytype = type_.accept(PythonType(self.current_proto))

        return (
            sname,
            gen_raw(
                """\
            def {{ sname }}(self, value: {{ pytype }}) -> int:
                return {{ inner_size }} * len(value)""",
                locals(),
            ),
        )

    def visit_list(self, type_: tir.List) -> t.Union[int, t.Tuple[str, pg.Node]]:
        sname = self.alloc_size_function()
        inner_sname, inner_helpers = checked_cast(tuple, type_.inner.accept(self))
        pytype = type_.accept(PythonType(self.current_proto))

        return (
            sname,
            pg.Section(
                [
                    inner_helpers,
                    gen_raw(
                        """\
                def {{ sname }}(self, value: {{ pytype }}) -> int:
                    result: int = 0
                    for x in value:
                        result += self.{{ inner_sname }}(x);
                    return result""",
                        locals(),
                    ),
                ]
            ),
        )

    def visit_detached_variant(
        self, type_: tir.DetachedVariant
    ) -> t.Union[int, t.Tuple[str, pg.Node]]:
        return self.handle_root(type_)

    def visit_virtual(self, type_: tir.Virtual) -> t.Union[int, t.Tuple[str, pg.Node]]:
        raise InternalError()

    def visit_struct(self, root: tir.Struct) -> t.Union[int, t.Tuple[str, pg.Node]]:
        return self.handle_root(root)

    def visit_variant(self, root: tir.Variant) -> t.Union[int, t.Tuple[str, pg.Node]]:
        raise InternalError()

    def visit_enum(self, root: tir.Enum) -> t.Union[int, t.Tuple[str, pg.Node]]:
        return self.handle_fixed_size(root)

    def alloc_size_function(self) -> str:
        result = f"_size_bytes{self.fname}{self.num}"
        self.num += 1
        return result

    def handle_fixed_size(self, type_: tir.Type) -> int:
        return checked_cast(st.Constant, type_.size).value

    def handle_root(self, type_: tir.Type) -> t.Union[int, t.Tuple[str, pg.Node]]:
        sname = self.alloc_size_function()
        pytype = type_.accept(PythonType(self.current_proto))
        return type_.size.accept(FieldSizerGeneratorHelper(sname, pytype))


@dataclasses.dataclass
class FieldSizerGeneratorHelper(st.SizeVisitor[t.Union[int, t.Tuple[str, pg.Node]]]):
    sname: str
    pytype: str

    def visit_constant(self, size: st.Constant) -> t.Union[int, t.Tuple[str, pg.Node]]:
        return size.value

    def visit_dynamic(self, size: st.Dynamic) -> t.Union[int, t.Tuple[str, pg.Node]]:
        return (
            self.sname,
            gen_raw(
                """\
            def {{ this.sname }}(self, value: {{ this.pytype }}) -> int:
                return value.size_bytes()""",
                locals(),
            ),
        )


@dataclasses.dataclass
class RootConstantGenerator(kir.RootConstantVisitor[pg.Node]):
    def visit_int_constant(self, constant: kir.RootIntConstant) -> pg.Node:
        return pg.Raw(f"{constant.name.name()}: int = {constant.value}")

    def visit_string_constant(self, constant: kir.RootStringConstant) -> pg.Node:
        # We encode the string as JSON in an attempt to correctly escape it
        pystring = json.dumps(constant.value)
        return pg.Raw(f"{constant.name.name()}: str = {pystring}")


@dataclasses.dataclass
class RootMarkerTypeGenerator(tir.RootTypeVisitor[pg.Node]):
    def handle_root(self, root: tir.RootType) -> pg.Node:
        class_name = get_marker_pyname(root, root.name.namespace())
        to_name = get_to_pyname(root, root.name.namespace())
        return gen_raw(
            """\
                class {{ class_name }}:
                    pass
                {{ to_name }} = {{ class_name }}()""",
            locals(),
        )

    def visit_struct(self, root: tir.Struct) -> pg.Node:
        return self.handle_root(root)

    def visit_variant(self, root: tir.Variant) -> pg.Node:
        return self.handle_root(root)

    def visit_enum(self, root: tir.Enum) -> pg.Node:
        return self.handle_root(root)


def gen_conversions(
    current_proto: QName, own: t.List[cir.RootConversion]
) -> t.List[pg.Node]:
    if not own:
        return []

    helpers = []
    overloads = []
    types = []
    main: t.List[pg.Node] = []

    for i, conv in enumerate(own):
        conversion_name = f"convert{i}"
        helpers.append(
            conv.accept_r(RootConversionGenerator(current_proto, conversion_name))
        )
        src_pytype, _, return_type = get_conversion_types(conv, current_proto)
        marker_pytype = get_marker_pyname(conv.target, current_proto)
        types.append((src_pytype, marker_pytype, return_type))

        overloads.append(
            gen_raw(
                """\
            @typing.overload
            def convert(src: {{ src_pytype }}, marker: {{ marker_pytype }}) -> {{ return_type }}:
                ...""",
                locals(),
            )
        )
        main.append(
            gen_raw(
                """\
            if isinstance(src, {{ src_pytype }}) and isinstance(marker, {{ marker_pytype }}):
                return {{ conversion_name }}(src)""",
                locals(),
            )
        )
    main.append(
        pg.Raw(
            'raise ValueError(f"Illegal conversion from {type(src)} to {type(marker)}")'
        )
    )

    srcs, markers, returns = map(", ".join, zip(*types))
    helpers.extend(overloads)
    helpers.append(
        pg.Function(
            "convert",
            [
                (pg.Type(f"typing.Union[{srcs}]"), "src"),
                (pg.Type(f"typing.Union[{markers}]"), "marker"),
            ],
            pg.Type(f"typing.Union[{returns}]"),
            pg.Section(main),
        )
    )
    return helpers


def get_conversion_types(
    conversion: cir.RootConversion, current_proto: QName
) -> t.Tuple[str, str, str]:
    src_pytype = conversion.src.accept(PythonType(current_proto))
    target_pytype = conversion.target.accept(PythonType(current_proto))
    if conversion.strength == cir.ConversionStrength.PARTIAL:
        return_type = f"typing.Optional[{target_pytype}]"
    else:
        return_type = target_pytype

    return src_pytype, target_pytype, return_type


@dataclasses.dataclass
class RootConversionGenerator(cir.RootConversionVisitor[pg.Node]):
    current_proto: QName
    conversion_name: str

    def get_types(self, conversion: cir.RootConversion) -> t.Tuple[str, str, str]:
        return get_conversion_types(conversion, self.current_proto)

    def visit_enum_conversion(self, conversion: cir.EnumConversion) -> pg.Node:
        src_pytype, target_pytype, return_type = self.get_types(conversion)

        return gen_raw(
            """\
            def {{ this.conversion_name }}(src: {{ src_pytype }}) -> {{ return_type }}:
                {%- for evm in conversion.mapping %}
                if src == {{ src_pytype }}.{{ evm.src.name }}:
                    {%- if evm.target is none %}
                    return None
                    {%- else %}
                    return {{ target_pytype }}.{{ evm.target.name }};
                    {%- endif %}
                {%- endfor %}
                raise ValueError('Enum held illegal value')""",
            locals(),
        )

    def visit_struct_conversion(self, conversion: cir.StructConversion) -> pg.Node:
        src_pytype, target_pytype, return_type = self.get_types(conversion)

        conversion_exprs: t.List[t.Tuple[str, str, str, bool]] = []
        for fname, field in conversion.target.get_owned():
            conversion_exprs.append(
                (
                    fname,
                    field.type_.accept(PythonType(self.current_proto)),
                    conversion.mapping[fname].accept(
                        ConversionExpressionGenerator(self.current_proto, "src")
                    ),
                    conversion.strength == cir.ConversionStrength.PARTIAL,
                )
            )

        return gen_raw(
            """\
            def {{ this.conversion_name }}(src: {{ src_pytype }}) -> {{ return_type }}:
                {%-for field_name, field_pytype, conversion_expr, partial in conversion_exprs %}
                {{ field_name }} = {{ conversion_expr }}
                {%- if partial %}
                if {{ field_name }} is None:
                    return None
                {%- endif %}
                {%-endfor %}
                return {{ target_pytype }} (
                {%-for field_name, _, _, _ in conversion_exprs %}
                    {{ field_name }}={{ field_name }},
                {%-endfor %}
                )""",
            locals(),
        )

    def visit_variant_conversion(self, conversion: cir.VariantConversion) -> pg.Node:
        src_pytype, target_pytype, return_type = self.get_types(conversion)
        visitor_name = get_visitor_name(conversion.src, self.current_proto)
        visitor_info = get_visitor_info(conversion.src)

        def conversion_expr(
            vvc: t.Optional[cir.VariantValueConversion]
        ) -> t.Tuple[t.Optional[str], bool]:
            if vvc is None:
                return None, True
            else:
                return (
                    vvc.conversion.accept(
                        ConversionExpressionGenerator(self.current_proto, "x")
                    ),
                    vvc.conversion.strength == cir.ConversionStrength.PARTIAL,
                )

        visitors = [
            (
                visitor_info[vvm.src.type_],
                vvm.src.type_.accept(PythonType(self.current_proto)),
                conversion_expr(vvm.target),
            )
            for vvm in conversion.mapping
        ]

        return gen_raw(
            """\
            def {{ this.conversion_name }}(src: {{ src_pytype }}) -> {{ return_type }}:
                class Visitor({{ visitor_name }}[{{ return_type }}]):
                    {%- for vname, vtype, (conversion_expr, partial) in visitors %}
                    def {{ vname }}(self, x: {{ vtype }}) -> {{ return_type }}:
                        {%- if conversion_expr is none %}
                        return None
                        {%- else %}
                        result = {{ conversion_expr }}
                        {%- if partial %}
                        if result is None:
                            return None
                        {%- endif %}
                        return {{ target_pytype }}(result)
                        {%- endif %}
                    {%- endfor %}
                return src.accept(Visitor())""",
            locals(),
        )


@dataclasses.dataclass
class ConversionExpressionGenerator(
    cir.ConversionVisitor[str], cir.FieldConversionVisitor[str]
):
    current_proto: QName
    src_expr: str

    def visit_identity_conversion(self, conversion: cir.IdentityConversion) -> str:
        return self.src_expr

    def visit_enum_conversion(self, conversion: cir.EnumConversion) -> str:
        return self.root_conversion_expr(conversion)

    def visit_struct_conversion(self, conversion: cir.StructConversion) -> str:
        return self.root_conversion_expr(conversion)

    def visit_int_default_field_conversion(
        self, conversion: cir.IntDefaultFieldConversion
    ) -> str:
        return f"{conversion.value}"

    def visit_enum_default_field_conversion(
        self, conversion: cir.EnumDefaultFieldConversion
    ) -> str:
        pytype = conversion.type_.accept(PythonType(self.current_proto))
        return f"{pytype}.{conversion.value.name}"

    def visit_transform_field_conversion(
        self, conversion: cir.TransformFieldConversion
    ) -> str:
        inner_src_expr = f"{self.src_expr}.{conversion.src_field}"
        return conversion.conversion.accept(
            ConversionExpressionGenerator(self.current_proto, inner_src_expr)
        )

    def visit_variant_conversion(self, conversion: cir.VariantConversion) -> str:
        return self.root_conversion_expr(conversion)

    def root_conversion_expr(self, conversion: cir.RootConversion) -> str:
        fname = localize(
            conversion.protocol.with_name("convert"), self.current_proto, "convert"
        )
        target_tag = get_to_pyname(conversion.target, self.current_proto)
        return f"{fname}({self.src_expr}, {target_tag})"


def qname_to_py(qname: QName) -> str:
    return ".".join(qname.parts)


def int_struct_pack_format(int_type: tir.Int) -> str:
    sign_modifier = struct_pack_sign(int_type.sign)
    endianness_prefix = struct_pack_endianness(int_type.endianness)
    width_spec = sign_modifier(int_struct_pack_width(int_type.width))
    return f"{endianness_prefix}{width_spec}"


def float_struct_pack_format(float_type: tir.Float) -> str:
    endianness_prefix = struct_pack_endianness(float_type.endianness)
    width_spec = float_struct_pack_width(float_type.width)
    return f"{endianness_prefix}{width_spec}"


def struct_pack_sign(sign: Sign) -> t.Callable[[str], str]:
    if sign == Sign.UNSIGNED:
        return str.upper
    else:
        return lambda x: x


def struct_pack_endianness(endianness: Endianness) -> str:
    if endianness == Endianness.BIG:
        return ">"
    else:
        return "<"


def int_struct_pack_width(width: int) -> str:
    if width == 1:
        return "b"
    elif width == 2:
        return "h"
    elif width == 4:
        return "i"
    elif width == 8:
        return "q"
    else:
        raise InternalError()


def float_struct_pack_width(width: int) -> str:
    if width == 4:
        return "f"
    elif width == 8:
        return "d"
    else:
        raise InternalError()


def get_local_struct(type_: tir.Struct) -> str:
    return type_.name.name()


def get_local_enum(type_: tir.Enum) -> str:
    return type_.name.name()


def get_local_variant(type_: tir.Variant) -> str:
    return type_.name.name()


def get_visitor_name(type_: tir.Variant, current_proto: QName) -> str:
    return localize(type_.name, current_proto, f"{get_local_variant(type_)}Visitor")


def get_visitor_info(type_: tir.Variant) -> t.Dict[tir.Struct, str]:
    variant_short_names = [variant.name.name() for variant in type_.tags.keys()]
    # If the short names are not unique, use numbers
    # TODO this isn't great, but is probably pretty unlikely
    good_names = len(set(variant_short_names)) == len(variant_short_names)

    def vp(x: str) -> str:
        return f"visit_{x}"

    return {
        variant: vp(pascal_to_snake(variant.name.name()) if good_names else str(i))
        for i, variant in enumerate(type_.tags.keys())
    }


def get_marker_pyname(type_: tir.RootType, current_proto: QName) -> str:
    return localize(type_.name, current_proto, f"Marker{type_.name.name()}")


def get_to_pyname(type_: tir.RootType, current_proto: QName) -> str:
    return localize(type_.name, current_proto, f"To{type_.name.name()}")


def localize(qname: QName, current_proto: QName, local_pytype: str) -> str:
    if qname.namespace() == current_proto:
        return local_pytype
    else:
        return qname_to_py(qname.namespace().with_name(local_pytype))


@dataclasses.dataclass
class PythonType(tir.TypeVisitor[str]):
    current_proto: QName

    def visit_int(self, type_: tir.Int) -> str:
        return "int"

    def visit_float(self, type_: tir.Float) -> str:
        return "float"

    def visit_array(self, type_: tir.Array) -> str:
        return self.visit_array_like(type_.inner)

    def visit_vector(self, type_: tir.Vector) -> str:
        return self.visit_array_like(type_.inner)

    def visit_list(self, type_: tir.List) -> str:
        return self.visit_array_like(type_.inner)

    def visit_array_like(self, inner: tir.Type) -> str:
        return f"typing.List[{inner.accept(self)}]"

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> str:
        return type_.variant.accept(self)

    def visit_virtual(self, type_: tir.Virtual) -> str:
        return type_.inner.accept(self)

    def visit_struct(self, root: tir.Struct) -> str:
        return self.localize(root.name, get_local_struct(root))

    def visit_variant(self, root: tir.Variant) -> str:
        return self.localize(root.name, get_local_variant(root))

    def visit_enum(self, root: tir.Enum) -> str:
        return self.localize(root.name, get_local_enum(root))

    def localize(self, qname: QName, pytype: str) -> str:
        return localize(qname, self.current_proto, pytype)


def gen_raw(template: str, env: t.Dict[str, t.Any]) -> pg.Raw:
    return pg.Raw(template_raw(template, {**globals(), **env}))
