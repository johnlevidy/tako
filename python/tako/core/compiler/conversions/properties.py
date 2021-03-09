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
from tako.core.compiler.conversions import mir
from tako.util.qname import QName
from tako.util.cast import unwrap
from tako.util.graph import Graph
from itertools import islice


@enum.unique
class ConversionStrength(enum.IntEnum):
    PARTIAL = enum.auto()
    TOTAL = enum.auto()
    COMPATIBLE = enum.auto()
    SUBSTITUTABLE = enum.auto()


def compute(
    conversion_graph: Graph[QName, mir.RootConversion],
) -> Graph[QName, ConversionStrength]:
    result: Graph[QName, ConversionStrength] = Graph()
    for src, target, conversion in conversion_graph:
        result.put(
            src, target, compute_conversion_properties(conversion, conversion_graph)
        )
    return result


def compute_conversion_properties(
    conversion: t.Union[mir.Conversion, mir.RootConversion],
    conversion_graph: Graph[QName, mir.RootConversion],
) -> ConversionStrength:
    if not conversion.accept(ConversionTotal(conversion_graph)):
        return ConversionStrength.PARTIAL
    if not conversion.accept(ConversionCompatible(conversion_graph)):
        return ConversionStrength.TOTAL
    if not conversion.accept(ConversionSubstitutable(conversion_graph)):
        return ConversionStrength.COMPATIBLE
    return ConversionStrength.SUBSTITUTABLE


@dataclasses.dataclass
class ConversionTotal(
    mir.ResolvingConversionVisitor[bool], mir.FieldConversionVisitor[bool]
):
    def visit_enum_conversion(self, conversion: mir.EnumConversion) -> bool:
        # An enum conversion is total if every mapping is defined,
        # which means for every source value there is a target value
        for evm in conversion.mapping:
            if evm.target is None:
                return False
        return True

    def visit_struct_conversion(self, conversion: mir.StructConversion) -> bool:
        # A struct conversion is total if for each target field, the conversion
        # which computes it is total
        for sfc in conversion.mapping.values():
            if not sfc.accept(self):
                return False
        return True

    def visit_variant_conversion(self, conversion: mir.VariantConversion) -> bool:
        # A variant conversion is very similar to an enum conversion.
        # It is total if a conversion is defined for every source tag,
        # and with the additional requirement that every conversion is total
        for vvc in conversion.mapping:
            if vvc.target is None or not vvc.target.conversion.accept(self):
                return False
        return True

    def visit_identity_conversion(self, conversion: mir.IdentityConversion) -> bool:
        # An identity conversion is always total, it can't fail
        return True

    def visit_int_default_field_conversion(
        self, conversion: mir.IntDefaultFieldConversion
    ) -> bool:
        # A default field conversion is always total because it just returns an integer
        return True

    def visit_enum_default_field_conversion(
        self, conversion: mir.EnumDefaultFieldConversion
    ) -> bool:
        # A default field conversion is always total because it just returns an integer
        return True

    def visit_transform_field_conversion(
        self, conversion: mir.TransformFieldConversion
    ) -> bool:
        # A transforming conversion is total if the underlying conversion is total
        return conversion.conversion.accept(self)


# Substitutable is the strictest of the relations.
# Any conversion that is substitutable must also be compatible and total.
# The check requires that the conversion is at least total.
@dataclasses.dataclass
class ConversionSubstitutable(mir.ResolvingConversionVisitor[bool]):
    def visit_enum_conversion(self, conversion: mir.EnumConversion) -> bool:
        if conversion.src.underlying_type != conversion.target.underlying_type:
            return False
        # An enum conversion is substitutable if each value of the source enum is unchanged
        # in the output
        # Precisely: for every name in the source enum NS represented by some tag value TS,
        # NS in the target enum must have the same tag value TS.
        # This means that every mapping must have the same name and value
        # in both the source and the target.
        for evm in conversion.mapping:
            # We can unwrap because the conversion is total
            if evm.src != unwrap(evm.target):
                return False
        return True

    def visit_struct_conversion(self, conversion: mir.StructConversion) -> bool:
        # Both structs must have the same number of fields
        if len(conversion.src.fields) != len(conversion.target.fields):
            return False

        # Iterate through the fields of both structs in lockstep (by index) and ensure
        # the conversion from src.fields[i] -> target.fields[i] is also substitutable.
        # Note that field renames don't matter -- a struct conversion is substitutable
        # on a type level in that a binary instance of the source type is a valid binary
        # instance of the target type.
        for sf, tf in zip(
            conversion.src.fields.keys(), conversion.target.fields.keys()
        ):
            if not check_field_conversion(conversion, sf, tf, self):
                return False

        return True

    def visit_variant_conversion(self, conversion: mir.VariantConversion) -> bool:
        # Again, a variant conversion is very similar to an enum conversion.
        # Instead of the names being equal, for the same tag, the conversion
        # has to be substitutable
        for vvc in conversion.mapping:
            # We can unwrap because the conversion is total
            vvm = unwrap(vvc.target)
            if vvc.src.value != vvm.target.value or not vvm.conversion.accept(self):
                return False
        return True

    def visit_identity_conversion(self, conversion: mir.IdentityConversion) -> bool:
        # An identity conversion is always substitutable
        return True


# Compatible is slightly weaker than substitutable.
# When a conversion is compatible, an instance of the source type can be interpreted
# as an instance of the target type, but may have trailing bytes not used
# in the target type representation.
# Roughly, the target type is a subset.
# The check requires that the conversion is at least total.
# TODO: one extenstion of this would involve constant fields. For example,
# if a struct had some constant field set to 0, and then the new version of the struct
# added an optional field to the end (an optional variant), where the tag
# was this previously constant field (and 0 indicated empty), then the layout of the
# struct won't change.
@dataclasses.dataclass
class ConversionCompatible(mir.ResolvingConversionVisitor[bool]):
    substitutable: ConversionSubstitutable = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.substitutable = ConversionSubstitutable(self.convs)

    def visit_enum_conversion(self, conversion: mir.EnumConversion) -> bool:
        # TODO: In theory, this is slightly too tight: the target enum could have a wider
        # underlying type
        return conversion.accept(self.substitutable)

    def visit_struct_conversion(self, conversion: mir.StructConversion) -> bool:
        # Unlike the substitutable relationship, the source struct can have more
        # fields than the target -- the conversion can drop fields
        if len(conversion.src.fields) < len(conversion.target.fields):
            return False

        # If the target type is empty, then the conversion is compatible
        if len(conversion.target.fields) == 0:
            return True

        # Iterate through the fields of both structs in lockstep (by index) and ensure
        # the conversion from src.fields[i] -> target.fields[i] is OK.
        # Note that field renames don't matter -- a struct conversion is substitutable
        # on a type level in that a binary instance of the source type is a valid binary
        # instance of the target type.
        src_field_names = list(conversion.src.fields.keys())
        target_field_names = list(conversion.target.fields.keys())
        ntf = len(target_field_names)
        for sf, tf in islice(zip(src_field_names, target_field_names), ntf - 1):
            # The conversion to all fields in the target but the last must be substitutable
            # This means they have no trailing bytes, which means all the subsequent fields
            # align.
            if not check_field_conversion(conversion, sf, tf, self.substitutable):
                return False

        # The last conversion only has to be compatible. This is what permits the
        # source type to be longer (in bytes) than the target type.
        # Note that of course the source type could also have more fields, but this is the
        # last field the target will ever know about.
        return check_field_conversion(
            conversion, src_field_names[ntf - 1], target_field_names[ntf - 1], self
        )

    def visit_variant_conversion(self, conversion: mir.VariantConversion) -> bool:
        # This is just like the substitutable check, except the underlying
        # conversion only has to be compatible
        for vvc in conversion.mapping:
            # We can unwrap because the conversion is total
            vvm = unwrap(vvc.target)
            if vvc.src.value != vvm.target.value or not vvm.conversion.accept(self):
                return False
        return True

    def visit_identity_conversion(self, conversion: mir.IdentityConversion) -> bool:
        # An identity conversion is always compatible
        return True


def check_field_conversion(
    conversion: mir.StructConversion,
    sf: str,
    tf: str,
    checker: mir.ResolvingConversionVisitor[bool],
) -> bool:
    # The only type of conversion permitted is a TransformFieldConversion
    conv = conversion.mapping[tf]
    if not isinstance(conv, mir.TransformFieldConversion):
        return False
    # The input for this field must be the source field at the same index
    if sf != conv.src_field:
        return False
    # Finally, the conversion itself must also be substitutable
    if not conv.conversion.accept(checker):
        return False

    return True
