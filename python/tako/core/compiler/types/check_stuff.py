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
from tako.util import int_model
from tako.util.qname import QName
from tako.core.error import Error


def run(types: t.Dict[QName, mir.RootType], type_order: t.List[QName]) -> t.List[Error]:
    errors: t.List[Error] = []
    for name in type_order:
        # Need 2 lines for mypy
        e: t.List[Error] = types[name].accept(CheckStuff(types))
        errors.extend(e)
    return errors


@dataclasses.dataclass
class CheckStuff(
    mir.RootTypeVisitor[t.List[Error]],
    mir.SeqTypeVisitor[t.List[Error]],
    mir.LengthVisitor[t.List[Error]],
    mir.VariantVisitor[t.List[Error]],
):
    types: t.Dict[QName, mir.RootType]
    defined_fields: t.Dict[str, mir.Type] = dataclasses.field(default_factory=dict)

    def visit_int(self, type_: mir.Int) -> t.List[Error]:
        if type_.width not in [1, 2, 4, 8]:
            return [Error(f"Illegal width: {type_.width}")]
        else:
            return []

    def visit_float(self, type_: mir.Float) -> t.List[Error]:
        if type_.width not in [4, 8]:
            return [Error(f"Illegal width: {type_.width}")]
        else:
            return []

    def visit_seq(self, type_: mir.Seq) -> t.List[Error]:
        return type_.inner.accept(self) + type_.length.accept(self)

    def visit_unbound_seq(self, type_: mir.UnboundSeq) -> t.List[Error]:
        return type_.inner.accept(self)

    def visit_fixed_length(self, length: mir.FixedLength) -> t.List[Error]:
        if length.length <= 0:
            return [Error(f"Illegal array length: {length.length}")]
        else:
            return []

    def visit_variable_length(self, length: mir.VariableLength) -> t.List[Error]:
        if length.length.name not in self.defined_fields:
            return [Error(f"Length not found: {length.length.name}")]
        length_type = self.defined_fields[length.length.name]
        if not isinstance(length_type, mir.Int):
            return [
                Error(
                    f"Type of array length expression (field: {length.length.name}) must be Int, found: {type(length_type)}\n"
                )
            ]

        return []

    def visit_detached_variant(self, type_: mir.DetachedVariant) -> t.List[Error]:
        if type_.tag.name not in self.defined_fields:
            return [Error(f"Tag not found: {type_.tag}")]
        tag_type = self.defined_fields[type_.tag.name]
        found = type_.variant.resolve(self.types).tag_type
        if tag_type != found:
            return [
                Error(
                    f"Type of variant tag expression not equal to variant tag type: expected: {tag_type} found: {found}"
                )
            ]

        return []

    def visit_virtual(self, type_: mir.Virtual) -> t.List[Error]:
        result = type_.inner.accept(self)
        if isinstance(type_.inner, mir.Virtual):
            result.append(
                Error(f"Virtual type contains cannot contain virtual inner type")
            )
        return result

    def visit_ref(self, type_: mir.Ref) -> t.List[Error]:
        return []

    def visit_struct(self, root: mir.Struct) -> t.List[Error]:
        errors: t.List[Error] = []
        for fname, ftype in root.fields.items():
            # 2 lines for mypy
            e: t.List[Error] = ftype.accept(self)
            errors += e
            self.defined_fields[fname] = ftype

        return errors

    def visit_variant(self, root: mir.Variant) -> t.List[Error]:
        result = root.accept_v(self)
        if sum(1 for x in root.types()) == 0:
            result.append(Error(f"Variant has no values: {root.name}"))
        return result

    def visit_fixed_variant(self, variant: mir.FixedVariant) -> t.List[Error]:
        result: t.List[Error] = []
        for struct, value in variant.tags.items():
            m = self.check_range(value, variant.tag_type)
            if m is not None:
                result.append(Error(f"Out of range enum value: {struct.name}: {m}"))
        return result

    def visit_hash_variant(self, variant: mir.HashVariant) -> t.List[Error]:
        return []

    def visit_enum(self, root: mir.Enum) -> t.List[Error]:
        result: t.List[Error] = []
        for key, value in root.variants.items():
            m = self.check_range(value, root.underlying_type)
            if m is not None:
                result.append(Error(f"Out of range enum value: {key}: {m}"))
        return result

    def check_range(self, value: int, type_: mir.Int) -> t.Optional[str]:
        rep_range = int_model.representable_range(type_.width, type_.sign)
        if value not in rep_range:
            return f"Value not in range: value = {value} range = {rep_range}"
        else:
            return None
