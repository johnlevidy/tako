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
from tako.core.internal_error import InternalError
from tako.util.qname import QName


"""
Computes a repr string, in a python-like syntax, of the given type.
The intention is for this string to uniquely describe the given type,
but to be as simple as possible in that there are no extraneous details which
can change without actually changing the representation of the type on the wire.
This is because these representations must be stable as Tako evolves.

The syntax used is of the form <type name>(<key>=<value>,).
There are no spaces ever. There are no quotes -- all strings involved must be legal names in Tako, and hence
cannot contain ",", "=", "(", or ")", which means there can't be any ambiguities.
A value can also be a nested mapping of the form {<key>=<value>,}. Again, "{" and "}" cannot appear in any
other context.
There are no trailing commas.

All root types have as their first field name=<fully qualified name>. The name is critical --
2 types that have the same fields but different names _are_ different types.
"""


@dataclasses.dataclass
class ReprStr(
    mir.RootTypeVisitor[str],
    mir.VariantVisitor[str],
    mir.SeqTypeVisitor[str],
    mir.LengthVisitor[str],
):
    types: t.Dict[QName, mir.RootType]

    def visit_int(self, type_: mir.Int) -> str:
        return f"Int(width={type_.width},sign={type_.sign.name},endianness={type_.endianness.name})"

    def visit_float(self, type_: mir.Float) -> str:
        return f"Float(width={type_.width},endianness={type_.endianness.name})"

    def repr_field_reference(self, fr: mir.FieldReference) -> str:
        return f"FieldReference(name={fr.name})"

    def visit_seq(self, type_: mir.Seq) -> str:
        # Note that the repr is done on the type before seq reduce
        # -- there is only Seq, but not List, Vector, or Array.
        # This is deliberate - the representation of the type is the intended to
        # be a representation that is as simple as possible, but conveys everything
        # needed to parse or serialize a type from a wire representation.
        # List, Vector, and Array do not impact the wire representation, and hence
        # are not used.
        length = type_.length.accept(self)
        return f"Seq(inner={type_.inner.accept(self)},length={length})"

    def visit_unbound_seq(self, type_: mir.UnboundSeq) -> str:
        raise InternalError()

    def visit_fixed_length(self, length: mir.FixedLength) -> str:
        return f"{length.length}"

    def visit_variable_length(self, length: mir.VariableLength) -> str:
        return self.repr_field_reference(length.length)

    def visit_detached_variant(self, type_: mir.DetachedVariant) -> str:
        variant = type_.variant.resolve(self.types)
        return f"DetachedVariant(variant={variant.accept(self)},tag={self.repr_field_reference(type_.tag)})"

    def visit_virtual(self, type_: mir.Virtual) -> str:
        # Virtual types contribute to the hash just like normal types, even though they have no
        # effect on the wire representation. They allow a type to represent that there is
        # some other data on the wire related to it -- virtual fields are parsed
        # using the context of the rest of the type.
        return f"Virtual(inner={type_.inner.accept(self)})"

    def visit_ref(self, type_: mir.Ref) -> str:
        return type_.resolve(self.types).accept(self)

    def visit_struct(self, root: mir.Struct) -> str:
        # Including the name of the fields is critical -- otherwise the struct Foo { x: int, y: int }
        # is the same as the struct Foo { y: int, x: int }.
        # Names provide meaning to fields.
        # Note that no derrived information, like the size or offset of fields is included. That could all
        # be computed from this and is extraneous.
        fields = ",".join(
            [f"{name}={type_.accept(self)}" for name, type_ in root.fields.items()]
        )
        return f"Struct(name={root.name},fields={{{fields}}})"

    def visit_variant(self, root: mir.Variant) -> str:
        return root.accept_v(self)

    def visit_fixed_variant(self, root: mir.FixedVariant) -> str:
        # Sort the variant by tag to ensure order doesn't matter
        pairs = sorted([(tag, sr) for sr, tag in root.tags.items()])
        variants = ",".join(
            [f"{tag}={value.resolve(self.types).accept(self)}" for tag, value in pairs]
        )
        return f"Variant(name={root.name},tag_type={root.tag_type.accept(self)},variants={{{variants}}})"

    def visit_hash_variant(self, root: mir.HashVariant) -> str:
        raise InternalError()

    def visit_enum(self, root: mir.Enum) -> str:
        # Like variant
        pairs = sorted([(value, name) for name, value in root.variants.items()])
        variants = ",".join([f"{value}={name}" for value, name in pairs])
        return f"Enum(name={root.name},underlying={root.underlying_type.accept(self)},variants={{{variants}}})"
