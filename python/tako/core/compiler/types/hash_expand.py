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
from tako.core.compiler.types import mir
from tako.core.error import Error
from tako.core.repr_str import ReprStr
from tako.util.qname import QName
import hashlib


@dataclasses.dataclass(frozen=True)
class Digest:
    repr_str: str
    repr_hash: str


def run(
    types: t.Dict[QName, mir.RootType], type_order: t.List[QName]
) -> t.Union[t.Dict[QName, Digest], t.List[Error]]:
    digest_map = {}
    for name in type_order:
        result = types[name].accept(HashExpand(types))
        if isinstance(result, Error):
            return [result]
        digest_map[name] = result.digest
        if result.replacement is not None:
            types[name] = result.replacement

    return digest_map


def sha256hex(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


@dataclasses.dataclass(frozen=True)
class HashExpandResult:
    digest: Digest
    replacement: t.Optional[mir.RootType]


@dataclasses.dataclass
class HashExpand(
    mir.RootTypeVisitor[t.Union[HashExpandResult, Error]],
    mir.VariantVisitor[t.Union[mir.FixedVariant, Error]],
):
    types: t.Dict[QName, mir.RootType]

    def digest(self, rt: mir.RootType) -> Digest:
        x = rt.accept(ReprStr(self.types))
        return Digest(repr_str=x, repr_hash=sha256hex(x))

    def visit_struct(self, root: mir.Struct) -> t.Union[HashExpandResult, Error]:
        return HashExpandResult(self.digest(root), None)

    def visit_variant(self, root: mir.Variant) -> t.Union[HashExpandResult, Error]:
        fixed = root.accept_v(self)
        if isinstance(fixed, Error):
            return fixed
        else:
            return HashExpandResult(self.digest(fixed), fixed)

    def visit_fixed_variant(
        self, variant: mir.FixedVariant
    ) -> t.Union[mir.FixedVariant, Error]:
        return variant

    def visit_hash_variant(
        self, variant: mir.HashVariant
    ) -> t.Union[mir.FixedVariant, Error]:
        # The width of the int is in bytes, which requires
        # 2x hex digits.
        tag_width_hex_digits = variant.tag_type.width * 2
        tag_map: t.Dict[mir.StructRef, int] = {}
        inv_tag_map: t.Dict[int, mir.StructRef] = {}
        for type_ in variant.types():
            hash_hex = self.digest(type_.resolve(self.types)).repr_hash
            short = int(hash_hex[:tag_width_hex_digits], 16)
            if short in inv_tag_map:
                return Error(
                    f"HashVariant {variant.name} has a collision: short hash = {hex(short)} values = [{inv_tag_map[short]}, {type_}]"
                )
            tag_map[type_] = short
            inv_tag_map[short] = type_

        return mir.FixedVariant(variant.name, variant.tag_type, tag_map)

    def visit_enum(self, root: mir.Enum) -> t.Union[HashExpandResult, Error]:
        return HashExpandResult(self.digest(root), None)
