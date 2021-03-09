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
from tako.core.compiler.types import mir, lir
from tako.util.cast import checked_cast, unwrap
from tako.core.compiler.types.master_fields import MasterField
from tako.core.compiler.types.hash_expand import Digest
from tako.core.internal_error import InternalError
from tako.core.compiler.types.size import SizeCalculator, RootSizeResult
from tako.core.compiler.types.trivial import CheckTrivialField
from tako.util.ranges import Range
from tako.util.qname import QName


def run(
    types: t.Dict[QName, mir.RootType],
    type_order: t.List[QName],
    master_field_map: t.Dict[QName, t.Dict[str, MasterField]],
    digest_map: t.Dict[QName, Digest],
    size_map: t.Dict[QName, RootSizeResult],
    enum_ranges: t.Dict[QName, t.List[Range]],
    tmap: t.Dict[QName, bool],
    own_types: t.List[QName],
    external_protocols: t.Set[QName],
) -> lir.ProtocolTypes:
    return lir.ProtocolTypes(
        types={
            name: type_.accept(
                FuseRootType(
                    types, master_field_map, digest_map, size_map, enum_ranges, tmap
                )
            )
            for name, type_ in types.items()
        },
        own=own_types,
        external_protocols=external_protocols,
    )


@dataclasses.dataclass(eq=False)
class FuseRootType(
    mir.RootTypeVisitor[lir.RootType],
    mir.VariantVisitor[lir.RootType],
    mir.LoweredTypeVisitor[lir.Type],
):
    types: t.Dict[QName, mir.RootType]
    master_field_map: t.Dict[QName, t.Dict[str, MasterField]]
    digest_map: t.Dict[QName, Digest]
    size_map: t.Dict[QName, RootSizeResult]
    enum_ranges: t.Dict[QName, t.List[Range]]
    tmap: t.Dict[QName, bool]

    def visit_struct(self, root: mir.Struct) -> lir.RootType:
        def assemble_master_field(fname: str) -> t.Optional[lir.MasterField]:
            mf = self.master_field_map[root.name].get(fname, None)
            if mf is None:
                return None
            else:
                return lir.MasterField(
                    mf.master_field,
                    root.fields[mf.master_field].accept(self),
                    mf.key_property,
                )

        return lir.Struct(
            size=self.size_map[root.name].size,
            trivial=self.tmap[root.name],
            name=root.name,
            digest=self.digest_map[root.name],
            fields={
                fname: lir.Field(
                    type_=ftype.accept(self),
                    offset=unwrap(self.size_map[root.name].offset).offset_map[fname],
                    master_field=assemble_master_field(fname),
                )
                for fname, ftype in root.fields.items()
            },
            tail_offset=unwrap(self.size_map[root.name].offset).tail_offset,
        )

    def visit_variant(self, root: mir.Variant) -> lir.RootType:
        return root.accept_v(self)

    def visit_fixed_variant(self, variant: mir.FixedVariant) -> lir.RootType:
        return lir.Variant(
            size=self.size_map[variant.name].size,
            trivial=self.tmap[variant.name],
            name=variant.name,
            digest=self.digest_map[variant.name],
            tag_type=checked_cast(lir.Int, variant.tag_type.accept(self)),
            tags={
                checked_cast(lir.Struct, sr.accept(self)): value
                for sr, value in variant.tags.items()
            },
        )

    def visit_hash_variant(self, variant: mir.HashVariant) -> lir.RootType:
        raise InternalError()

    def visit_enum(self, root: mir.Enum) -> lir.RootType:
        return lir.Enum(
            size=self.size_map[root.name].size,
            trivial=self.tmap[root.name],
            name=root.name,
            digest=self.digest_map[root.name],
            underlying_type=checked_cast(lir.Int, root.underlying_type.accept(self)),
            variants=root.variants,
            valid_ranges=self.enum_ranges[root.name],
        )

    def visit_int(self, type_: mir.Int) -> lir.Type:
        return lir.Int(
            size=type_.accept(SizeCalculator(self.size_map)),
            trivial=type_.accept(CheckTrivialField(self.tmap)),
            width=type_.width,
            sign=type_.sign,
            endianness=type_.endianness,
        )

    def visit_float(self, type_: mir.Float) -> lir.Type:
        return lir.Float(
            size=type_.accept(SizeCalculator(self.size_map)),
            trivial=type_.accept(CheckTrivialField(self.tmap)),
            width=type_.width,
            endianness=type_.endianness,
        )

    def visit_array(self, type_: mir.Array) -> lir.Type:
        return lir.Array(
            size=type_.accept(SizeCalculator(self.size_map)),
            trivial=type_.accept(CheckTrivialField(self.tmap)),
            inner=type_.inner.accept(self),
            length=type_.length,
        )

    def visit_vector(self, type_: mir.Vector) -> lir.Type:
        return lir.Vector(
            size=type_.accept(SizeCalculator(self.size_map)),
            trivial=type_.accept(CheckTrivialField(self.tmap)),
            inner=type_.inner.accept(self),
            length=type_.length,
        )

    def visit_list(self, type_: mir.List) -> lir.Type:
        return lir.List(
            size=type_.accept(SizeCalculator(self.size_map)),
            trivial=type_.accept(CheckTrivialField(self.tmap)),
            inner=type_.inner.accept(self),
            length=type_.length,
        )

    def visit_detached_variant(self, type_: mir.DetachedVariant) -> lir.Type:
        return lir.DetachedVariant(
            size=type_.accept(SizeCalculator(self.size_map)),
            trivial=type_.accept(CheckTrivialField(self.tmap)),
            variant=checked_cast(lir.Variant, type_.variant.accept(self)),
            tag=type_.tag,
        )

    def visit_virtual(self, type_: mir.Virtual) -> lir.Type:
        return lir.Virtual(
            size=type_.accept(SizeCalculator(self.size_map)),
            trivial=type_.accept(CheckTrivialField(self.tmap)),
            inner=type_.inner.accept(self),
        )

    def visit_ref(self, type_: mir.Ref) -> lir.Type:
        return type_.resolve(self.types).accept(self)
