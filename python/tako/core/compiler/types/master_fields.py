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
import enum
from tako.core.compiler.types import mir
from tako.util.qname import QName
from tako.core.error import Error
from tako.core.internal_error import InternalError


@dataclasses.dataclass(frozen=True)
class MasterField:
    master_field: str
    key_property: KeyProperty


@dataclasses.dataclass(frozen=True)
class DeterminedField:
    determined_field: str
    key_property: KeyProperty


@enum.unique
class KeyProperty(enum.Enum):
    VARIANT_TAG = enum.auto()
    SEQ_LENGTH = enum.auto()


def run(
    types: t.Dict[QName, mir.RootType], type_order: t.List[QName]
) -> t.Union[t.Dict[QName, t.Dict[str, MasterField]], t.List[Error]]:
    result = {}
    errors = []
    for name in type_order:
        maybe = types[name].accept(MasterFields())
        if isinstance(maybe, Error):
            errors.append(maybe)
        elif isinstance(maybe, dict):
            result[name] = maybe

    if errors:
        return errors
    else:
        return result


@dataclasses.dataclass
class MasterFields(mir.RootTypeVisitor[t.Union[Error, t.Dict[str, MasterField], None]]):
    def visit_struct(
        self, root: mir.Struct
    ) -> t.Union[Error, t.Dict[str, MasterField], None]:
        return master_fields(root)

    def visit_variant(
        self, root: mir.Variant
    ) -> t.Union[Error, t.Dict[str, MasterField], None]:
        return None

    def visit_enum(
        self, root: mir.Enum
    ) -> t.Union[Error, t.Dict[str, MasterField], None]:
        return None


# Map from a field A to a field B where the value of A (slave field) is determined by the the value
# of field B (master field).
# For example, if a struct has these fields: {"len": li32, "data", Seq(li32, this.len)},
# then this function would return {"len": "data"} because the value of len is determined
# by the value in data.
# This is needed for generating builders: should a given field be included in the generated
# constructor, or should its value be generated from a later field?
# This is the opposite of parsing, where the earlier field is used to parse the later
# field.
# Note that this encoding doesn't allow for a field to determine multiple other fields -- for example
# this sort of matrix type:
#     Matrix = Struct(
#         cols=u8,
#         rows=u8,
#         data=Seq(Seq(i8, this.cols), this.rows),
#     )
# (There is no way to specifiy which "part" of a field determines what other field.)
# TODO: this is a limitiation, but probably doesn't matter. It also
# complicates the generated code. For example, the above matrix type in C++ can be represented in
# C++ with a vector<vector<int8_t>>. However, the invariant (implicit in the above matrix definition)
# that each row has the same number of columns is not present.
# As such, a compliant builder would have to check each row to determine if it had the same number of columns,
# and fail to build the protocol if they didn't!
def master_fields(struct: mir.Struct) -> t.Union[Error, t.Dict[str, MasterField]]:
    field_to_master: t.Dict[str, MasterField] = {}
    for fname, ftype in struct.fields.items():
        determined_field = ftype.accept(DeterminedFieldFinder())
        if isinstance(determined_field, Error):
            return Error(f"Field: error {fname}: {determined_field}")
        elif determined_field is not None:
            master = MasterField(fname, determined_field.key_property)
            if determined_field.determined_field in field_to_master:
                return Error(
                    f"{determined_field.determined_field} has multiple masters: {master} and {field_to_master[determined_field.determined_field]}"
                )
            else:
                field_to_master[determined_field.determined_field] = master
    return field_to_master


"""
For a given type, returns a DeterminedField indicating the field the given type determines,
and how.
For example, consider a type x = Seq(Int(...), VariableLength(FieldReference("bob"))).
x.accept(DeterminedFieldFinder())
will return DeterminedField("bob", KeyProperty.SEQ_LENGTH), indicating that the field
of type x determines the field "bob" using its length.
"""


@dataclasses.dataclass
class DeterminedFieldFinder(
    mir.SeqTypeVisitor[t.Union[Error, DeterminedField, None]],
    mir.LengthVisitor[t.Union[Error, DeterminedField, None]],
):
    def visit_int(self, type_: mir.Int) -> t.Union[Error, DeterminedField, None]:
        return None

    def visit_float(self, type_: mir.Float) -> t.Union[Error, DeterminedField, None]:
        return None

    def visit_seq(self, type_: mir.Seq) -> t.Union[Error, DeterminedField, None]:
        inner_result = type_.inner.accept(self)
        if inner_result is not None:
            return Error(
                f"Inner part of sequence cannot determine any fields: {inner_result}"
            )
        else:
            return type_.length.accept(self)

    def visit_fixed_length(
        self, length: mir.FixedLength
    ) -> t.Union[Error, DeterminedField, None]:
        return None

    def visit_variable_length(
        self, length: mir.VariableLength
    ) -> t.Union[Error, DeterminedField, None]:
        return DeterminedField(length.length.name, KeyProperty.SEQ_LENGTH)

    def visit_unbound_seq(
        self, type_: mir.UnboundSeq
    ) -> t.Union[Error, DeterminedField, None]:
        raise InternalError()

    def visit_detached_variant(
        self, type_: mir.DetachedVariant
    ) -> t.Union[Error, DeterminedField, None]:
        return DeterminedField(type_.tag.name, KeyProperty.VARIANT_TAG)

    def visit_virtual(
        self, type_: mir.Virtual
    ) -> t.Union[Error, DeterminedField, None]:
        # No field can depend on a virtual
        # A virtual might depend on other fields, but when building a message,
        # virtual fields are not considered (no field in the message has to be set
        # based on the value of a virtual field)
        return None

    def visit_ref(self, type_: mir.Ref) -> t.Union[Error, DeterminedField, None]:
        return None
