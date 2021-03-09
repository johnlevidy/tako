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
from tako.core.sir import Protocol, tir, kir, cir
from tako.util.qname import QName
import tako.core.size_types as st
from tako.generators.generator import Generator


class LsirGenerator(Generator):
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def generate_into(self, proto: Protocol, out_dir: Path, args: t.Any) -> None:
        dform = {
            "name": str(proto.name),
            "external_protocols": [str(x) for x in proto.types.external_protocols],
            "constants": {
                cname.name(): cvalue.accept(RootConstantLsir())
                for cname, cvalue in proto.constants.constants.items()
            },
            "types": {
                tname.name(): proto.types.types[tname].accept_rtv(RootTypeLsir())
                for tname in proto.types.own
            },
            "conversions": [
                rc.accept_r(RootConversionLsir()) for rc in proto.conversions.own
            ],
        }
        with (out_dir / Path(str(proto.name) + ".json")).open("w") as out:
            json.dump(dform, out, indent=4)

    def list_outputs(
        self, proto_qname: QName, args: t.Any
    ) -> t.Generator[Path, None, None]:
        return
        yield

    def generate_dir(self, proto: Protocol, dr: Path) -> None:
        pass


@dataclasses.dataclass
class RootTypeLsir(tir.RootTypeVisitor[t.Dict[str, t.Any]]):
    def common(
        self, root: tir.RootType, extra: t.Dict[str, t.Any]
    ) -> t.Dict[str, t.Any]:
        return {
            "kind": type(root).__name__,
            "size": root.size.accept(SizeLsir()),
            "trivial": root.trivial,
            "digest": {
                "repr_str": root.digest.repr_str,
                "repr_hash": root.digest.repr_hash,
            },
            **extra,
        }

    def visit_struct(self, root: tir.Struct) -> t.Dict[str, t.Any]:
        return self.common(
            root,
            {
                "fields": {
                    fname: {
                        "type": field.type_.accept(TypeLsir()),
                        "offset": {
                            "base": field.offset.base,
                            "offset": field.offset.offset,
                        },
                        "master_field": {}
                        if field.master_field is None
                        else {
                            "name": field.master_field.master_field,
                            "key_property": field.master_field.key_property.name,
                        },
                    }
                    for fname, field in root.fields.items()
                },
                "tail_offset": {
                    "base": root.tail_offset.base,
                    "offset": root.tail_offset.offset,
                },
            },
        )

    def visit_variant(self, root: tir.Variant) -> t.Dict[str, t.Any]:
        return self.common(
            root,
            {
                "tag_type": root.tag_type.accept(TypeLsir()),
                "variants": {
                    f"{struct.name}": value for struct, value in root.tags.items()
                },
            },
        )

    def visit_enum(self, root: tir.Enum) -> t.Dict[str, t.Any]:
        return self.common(
            root,
            {
                "underlying_type": root.underlying_type.accept(TypeLsir()),
                "variants": {name: value for name, value in root.variants.items()},
                "valid_ranges": [
                    {"start": r.start, "end": r.end} for r in root.valid_ranges
                ],
            },
        )


class TypeLsir(
    tir.TypeVisitor[t.Dict[str, t.Any]], tir.LengthVisitor[t.Dict[str, t.Any]]
):
    def common(self, type_: tir.Type, extra: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        return {
            "kind": type(type_).__name__,
            "size": type_.size.accept(SizeLsir()),
            "trivial": type_.trivial,
            **extra,
        }

    def visit_int(self, type_: tir.Int) -> t.Dict[str, t.Any]:
        return self.common(
            type_,
            {
                "width": type_.width,
                "sign": type_.sign.name,
                "endianness": type_.endianness.name,
            },
        )

    def visit_float(self, type_: tir.Float) -> t.Dict[str, t.Any]:
        return self.common(
            type_, {"width": type_.width, "endianness": type_.endianness.name}
        )

    def visit_array(self, type_: tir.Array) -> t.Dict[str, t.Any]:
        return self.common(
            type_,
            {
                "inner": type_.inner.accept(self),
                "length": self.handle_fixed_length(type_.length),
            },
        )

    def visit_vector(self, type_: tir.Vector) -> t.Dict[str, t.Any]:
        return self.common(
            type_,
            {
                "inner": type_.inner.accept(self),
                "length": self.handle_field_reference(type_.length),
            },
        )

    def visit_list(self, type_: tir.List) -> t.Dict[str, t.Any]:
        return self.common(
            type_,
            {"inner": type_.inner.accept(self), "length": type_.length.accept(self)},
        )

    def visit_detached_variant(self, type_: tir.DetachedVariant) -> t.Dict[str, t.Any]:
        return self.common(
            type_,
            {
                "variant": type_.variant.accept(TypeLsir()),
                "tag": self.handle_field_reference(type_.tag),
            },
        )

    def visit_virtual(self, type_: tir.Virtual) -> t.Dict[str, t.Any]:
        return self.common(type_, {"inner": type_.inner.accept(self)})

    def handle_field_reference(self, ref: tir.FieldReference) -> t.Dict[str, t.Any]:
        return {"reference": ref.name}

    def handle_fixed_length(self, length: int) -> t.Dict[str, t.Any]:
        return {"fixed": f"{length}"}

    def visit_fixed_length(self, length: tir.FixedLength) -> t.Dict[str, t.Any]:
        return self.handle_fixed_length(length.length)

    def visit_variable_length(self, length: tir.VariableLength) -> t.Dict[str, t.Any]:
        return self.handle_field_reference(length.length)

    def handle_root_type(self, root: tir.RootType) -> t.Dict[str, t.Any]:
        return {"name": f"{root.name}", **self.common(root, {})}

    def visit_struct(self, root: tir.Struct) -> t.Dict[str, t.Any]:
        return self.handle_root_type(root)

    def visit_variant(self, root: tir.Variant) -> t.Dict[str, t.Any]:
        return self.handle_root_type(root)

    def visit_enum(self, root: tir.Enum) -> t.Dict[str, t.Any]:
        return self.handle_root_type(root)


@dataclasses.dataclass
class SizeLsir(st.SizeVisitor[t.Dict[str, t.Any]]):
    def common(self, size: st.Size, extra: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        return {"kind": type(size).__name__, **extra}

    def visit_constant(self, expr: st.Constant) -> t.Dict[str, t.Any]:
        return self.common(expr, {"value": expr.value})

    def visit_dynamic(self, expr: st.Dynamic) -> t.Dict[str, t.Any]:
        return self.common(expr, {})


@dataclasses.dataclass
class RootConstantLsir(kir.RootConstantVisitor[t.Dict[str, t.Any]]):
    def common(
        self, constant: kir.RootConstant, extra: t.Dict[str, t.Any]
    ) -> t.Dict[str, t.Any]:
        return {"kind": type(constant).__name__, **extra}

    def visit_int_constant(self, constant: kir.RootIntConstant) -> t.Dict[str, t.Any]:
        return self.common(
            constant,
            {"type": constant.type_.accept(TypeLsir()), "value": f"{constant.value}"},
        )

    def visit_string_constant(
        self, constant: kir.RootStringConstant
    ) -> t.Dict[str, t.Any]:
        return self.common(constant, {"value": f"{constant.value}"})


@dataclasses.dataclass
class RootConversionLsir(
    cir.RootConversionVisitor[t.Dict[str, t.Any]],
    cir.FieldConversionVisitor[t.Dict[str, t.Any]],
):
    def common(
        self, conversion: cir.RootConversion, extra: t.Dict[str, t.Any]
    ) -> t.Dict[str, t.Any]:
        return {
            "kind": type(conversion).__name__,
            "src": conversion.src.accept(TypeLsir()),
            "target": conversion.target.accept(TypeLsir()),
            "strength": conversion.strength.name,
            **extra,
        }

    def visit_enum_conversion(
        self, conversion: cir.EnumConversion
    ) -> t.Dict[str, t.Any]:
        return self.common(
            conversion,
            {
                "mapping": [
                    {
                        "src": self.handle_enum_value(evm.src),
                        "target": self.handle_enum_value(evm.target),
                    }
                    for evm in conversion.mapping
                ]
            },
        )

    def handle_enum_value(self, ev: t.Optional[cir.EnumValue]) -> t.Dict[str, t.Any]:
        if ev:
            return {"name": ev.name, "value": ev.value}
        else:
            return {}

    def visit_struct_conversion(
        self, conversion: cir.StructConversion
    ) -> t.Dict[str, t.Any]:
        return self.common(
            conversion,
            {
                "mapping": {
                    target_field_name: sfc.accept(self)
                    for target_field_name, sfc in conversion.mapping.items()
                }
            },
        )

    def common_fc(
        self,
        conversion: cir.FieldConversion,
        extra: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Dict[str, t.Any]:
        result = {"type": type(conversion).__name__}
        result.update(extra or {})
        return result

    def visit_int_default_field_conversion(
        self, conversion: cir.IntDefaultFieldConversion
    ) -> t.Dict[str, t.Any]:
        return self.common_fc(
            conversion,
            {"type": conversion.type_.accept(TypeLsir()), "value": conversion.value},
        )

    def visit_enum_default_field_conversion(
        self, conversion: cir.EnumDefaultFieldConversion
    ) -> t.Dict[str, t.Any]:
        return self.common_fc(
            conversion,
            {
                "type": conversion.type_.accept(TypeLsir()),
                "value": self.handle_enum_value(conversion.value),
            },
        )

    def visit_transform_field_conversion(
        self, conversion: cir.TransformFieldConversion
    ) -> t.Dict[str, t.Any]:
        return self.common_fc(
            conversion,
            {
                "src_field": conversion.src_field,
                "conversion": conversion.conversion.accept(ConversionLsir()),
            },
        )

    def visit_variant_conversion(
        self, conversion: cir.VariantConversion
    ) -> t.Dict[str, t.Any]:
        return self.common(
            conversion,
            {
                "mapping": [
                    {
                        "src": self.handle_variant_value(vvm.src),
                        "target": self.handle_variant_value_conversion(vvm.target),
                    }
                    for vvm in conversion.mapping
                ]
            },
        )

    def handle_variant_value(self, vv: cir.VariantValue) -> t.Dict[str, t.Any]:
        return {"type": vv.type_.accept(TypeLsir()), "value": vv.value}

    def handle_variant_value_conversion(
        self, vvc: t.Optional[cir.VariantValueConversion]
    ) -> t.Dict[str, t.Any]:
        if vvc:
            return {
                "target": self.handle_variant_value(vvc.target),
                "conversion": vvc.conversion.accept(ConversionLsir()),
            }
        else:
            return {}


@dataclasses.dataclass
class ConversionLsir(cir.ConversionVisitor[t.Dict[str, t.Any]]):
    def common(
        self, conversion: cir.Conversion, extra: t.Dict[str, t.Any]
    ) -> t.Dict[str, t.Any]:
        return {
            "kind": type(conversion).__name__,
            "src": conversion.src.accept(TypeLsir()),
            "target": conversion.target.accept(TypeLsir()),
            "strength": conversion.strength.name,
            **extra,
        }

    def visit_enum_conversion(
        self, conversion: cir.EnumConversion
    ) -> t.Dict[str, t.Any]:
        return self.common(conversion, {})

    def visit_struct_conversion(
        self, conversion: cir.StructConversion
    ) -> t.Dict[str, t.Any]:
        return self.common(conversion, {})

    def visit_variant_conversion(
        self, conversion: cir.VariantConversion
    ) -> t.Dict[str, t.Any]:
        return self.common(conversion, {})

    def visit_identity_conversion(
        self, conversion: cir.IdentityConversion
    ) -> t.Dict[str, t.Any]:
        return self.common(conversion, {})
