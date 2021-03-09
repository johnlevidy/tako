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
import tako.core.types as pt
from tako.core.error import Error
from tako.util.cast import unwrap
from tako.util.qname import QName
from tako.util.graph import Graph
import dataclasses
import re


def valid_identifier(name: str) -> bool:
    # Note that a valid identifier cannot start or end with _
    # This creates a reserved namespace which the code generators can
    # freely use.
    # The leading _ namespace is for use by the code generators (i.e. the code generators can assume that
    # nothing nothing they see will ever start with _).
    # The tako core can use the trailing _ namespace. It must never create any name with
    # a leading _, and can assume that all names as input have neither a trailing or leading _.
    # TODO: prohibit the View suffix? Potentially (at least for the C++ backend)
    # there could be name conflicts
    # TODO: consider reserving a subset of names like parse, build, and build_into
    # so the generated classes are free to use these names.
    # Maybe even reserve entire prefixes like raw so we can make methods raw_some_enum() to get the
    # raw enum value.
    regex = "^[A-Za-z][A-Za-z0-9_]*(?<!_)$"
    # Keywords in the target languages are not permitted as identifiers
    # In addition, we reserve a small space of keywords for use by the code generators
    keywords = set(
        [
            # Reserved for use by the code generators
            "parse",
            "build",
            "size_bytes",
            "serialize",
            "serialize_into",
            # Language keywords
            "for",
            "while",
            "in",
            "auto",
            "const",
            "volatile",
            "def",
            "void",
            "not",
            "and",
            "or",
            "None",
            "return",
            "int",
            "long",
            "signed",
            "unsigned",
            "double",
            "float",
            "bool",
            "class",
            "struct",
            "public",
            "private",
            "protected",
            "final",
            "default",
            "new",
            "delete",
        ]
    )
    illegal_suffix = ("View", "Tag")
    return (
        (name not in keywords)
        and (re.search(regex, name) is not None)
        and (not name.endswith(illegal_suffix))
    )


def valid_qname(name: QName) -> bool:
    return all([valid_identifier(x) for x in name.parts])


def run(proto_proto: pt.ProtoProto) -> t.Union[pt.ProtocolDef, t.List[Error]]:
    return TypeChecker.build(proto_proto).type_check()


@dataclasses.dataclass
class TypeChecker(
    pt.TypeVisitor, pt.ConversionSpecifierVisitor[None], pt.ConversionVisitor[None]
):
    # proto_qname is the name of the protocol we are building
    # pending_protocols is all the protocols that have to be typechecked.
    proto_qname: QName
    current_protocol: pt.ProtoProto
    pending_protocols: t.Set[QName] = dataclasses.field(default_factory=set)

    checked: t.Set[QName] = dataclasses.field(default_factory=set)
    types: t.Dict[QName, pt.RootType] = dataclasses.field(default_factory=dict)
    constants: t.Dict[QName, pt.RootConstant] = dataclasses.field(default_factory=dict)
    conversions: Graph[QName, pt.ResolvedConversion] = dataclasses.field(
        default_factory=Graph
    )

    errors: t.List[Error] = dataclasses.field(default_factory=list)
    context: t.List[QName] = dataclasses.field(default_factory=list)
    pending: t.Set[QName] = dataclasses.field(default_factory=set)
    type_sources: t.Dict[QName, pt.Type] = dataclasses.field(default_factory=dict)
    proto_sources: t.Dict[QName, pt.ProtoProto] = dataclasses.field(
        default_factory=dict
    )

    @staticmethod
    def build(proto_proto: pt.ProtoProto) -> TypeChecker:
        return TypeChecker(proto_proto.name, proto_proto)

    def type_check(self) -> t.Union[pt.ProtocolDef, t.List[Error]]:
        self.check_protocol(self.current_protocol)

        if not self.errors:
            return pt.ProtocolDef(
                self.proto_qname,
                self.types,
                # The insertion order into self.types is a reverse topological sort
                # of the type dependency graph (leaf types first, types which depend on other
                # types last).
                list(self.types.keys()),
                self.constants,
                self.conversions,
            )
        else:
            return self.errors

    def check_protocol(self, proto_proto: pt.ProtoProto) -> None:
        if proto_proto.name in self.pending_protocols:
            self.error(
                f"Found cycle while type checking: {proto_proto.name}: pending: {self.pending_protocols}\n"
            )
            return

        # Bail if the protocol name is not valid - any further checks are hard to reason about
        if not valid_qname(proto_proto.name):
            self.error(f"Invalid protocol name: {proto_proto.name}")
            return

        # Underscores cannot be used in a protocol name. This means that it can be converted
        # to snake_case without introducing a conflict.
        if "_" in proto_proto.name.name():
            self.error(f"Protocol name cannot contain _: {proto_proto.name.name()}")
            return

        self.pending_protocols.add(proto_proto.name)
        self.push_context_qname(proto_proto.name)
        old_protocol = self.current_protocol
        self.current_protocol = proto_proto

        for name, type_ in proto_proto.defined_types.items():
            self.check_own_root_type(type_, name)
        for name, constant in proto_proto.defined_constants.items():
            self.check_own_root_constant(constant, name)
        for conversion_specifier in proto_proto.defined_conversions:
            conversion_specifier.accept_cs(self)

        self.current_protocol = old_protocol
        self.pop_context()
        self.pending_protocols.remove(proto_proto.name)

    def push_context_qname(self, name: QName) -> None:
        self.context.append(name)

    def context_with(self, name: str) -> QName:
        return self.context[-1].with_name(name)

    def push_context_with_name(self, name: str) -> None:
        self.push_context_qname(self.context_with(name))

    def pop_context(self) -> QName:
        return self.context.pop()

    def error(self, desc: str) -> None:
        self.errors.append(
            Error(
                desc,
                context=self.context[-1],
                source_type=self.current_protocol.definition_source,
            )
        )

    def check_declared_name(self, name: t.Optional[str], declared_name: str) -> bool:
        if name is None:
            self.error(
                f"Type name not set; this type must be declared as a mebmer of some protocol class.\n"
                f"Note: declared name is: {declared_name}"
            )
            return False
        if declared_name != name:
            self.error(
                f"Type name and declared name do not match: {declared_name} != {name}"
            )
            return False

        return True

    def check_own_root_type(self, type_: pt.RootType, declared_name: str) -> None:
        if self.check_declared_name(type_.name, declared_name):
            self.check_root_type(type_)

    def check_own_root_constant(
        self, constant: pt.RootConstant, declared_name: str
    ) -> None:
        if not self.check_declared_name(constant.name, declared_name):
            return

        qname = constant.qualified_name()
        ctc = ConstantTypeChecker(self)
        self.push_context_qname(qname)
        constant.accept(ctc)
        self.pop_context()

        if unwrap(constant.proto_proto).name != self.current_protocol.name:
            self.error(
                f"Constant is from external protocol: {unwrap(constant.proto_proto).name}"
            )
        elif unwrap(constant.proto_proto).name == self.proto_qname:
            # Only add constants from the root protocol
            self.constants[qname] = constant

    def check_name(
        self, name: t.Optional[str], proto_proto: t.Optional[pt.ProtoProto]
    ) -> bool:
        if name is None:
            self.error(
                f"Type name is not set; this type must be declared as a mebmer of some protocol class."
            )
            return False
        if proto_proto is None:
            self.error(
                f"Type proto_proto is not set; this type must be declared as a mebmer of some protocol class."
            )
            return False
        if not valid_identifier(name):
            self.error(f"Invalid type name: {name}")
            return False
        if not valid_qname(proto_proto.name):
            self.error(f"Invalid type protocol: {proto_proto.name}")
            return False

        return True

    def check_root_type(self, type_: pt.RootType) -> None:
        # Ensure the the name and protocol for the type is defined.
        # Bail if it isn't so further checking can rely on the type at least
        # having a fully qualified name
        if not self.check_name(type_.name, type_.proto_proto):
            return

        if type_.proto_proto is None:
            self.error(f"Type has no no owning protocol object")
            return

        # Check One Definition Rule (ODR) for protocol objects
        if type_.proto_proto.name in self.proto_sources:
            prior_proto_definition = self.proto_sources[type_.proto_proto.name]
            if type_.proto_proto is not prior_proto_definition:
                self.error(
                    f"Multiple definitions for: {type_.proto_proto.name}\n"
                    f"Note: current definition is: {type_.proto_proto}\n"
                    f"Note: prior definition is: {prior_proto_definition}"
                )
                return

        self.proto_sources[unwrap(type_.proto_proto).name] = type_.proto_proto

        qname = type_.qualified_name()
        # Check for loops
        if qname in self.pending:
            self.error(f"Found cycle while type checking: {qname}\n")
            return

        # Make sure that if 2 types have the same qualified name, they originate
        # from the same python object
        # (Roughly, ODR -- the One Definition Rule)
        if qname in self.type_sources and type_ is not self.type_sources[qname]:
            self.error(
                f"Multiple definitions for: {qname}\n"
                f"Note: current definition is: {type_}\n"
                f"Note: prior definition is: {self.type_sources[qname]}"
            )
            return

        self.type_sources[qname] = type_

        # If we have checked this type already, do not check it again
        # Note that this comes after the ODR check, so if this is true
        # then we have checked a type with the same name and which is
        # actually the same type.
        if qname in self.checked:
            return

        # We now have a type that:
        # (a) has a valid name and protocol (has a valid qname)
        # (b) has no prior definition
        # (c) has not been typechecked yet
        # There are 2 cases:
        # (a) This type is in the protocol we are currently checking.
        #     In this case, just check it normally
        # (b) This type is in some new protocol we haven't checked yet
        #     Now, we have to type check the entire other protocol.
        if type_.proto_proto.name == self.current_protocol.name:
            rtc = RootTypeChecker(self)
            self.pending.add(qname)
            self.push_context_qname(qname)
            type_.accept_rtv(rtc)
            self.pop_context()
            self.pending.remove(qname)

            self.types[qname] = type_
            self.checked.add(qname)
        else:
            self.check_protocol(type_.proto_proto)

    def accept_with_context(self, type_: pt.Type, qname: QName) -> None:
        self.push_context_qname(qname)
        type_.accept(self)
        self.pop_context()

    def accept_append_context(self, type_: pt.Type, name: str) -> None:
        self.accept_with_context(type_, self.context_with(name))

    def visit_int(self, type_: pt.Int) -> None:
        pass

    def visit_float(self, type_: pt.Float) -> None:
        pass

    def visit_seq(self, type_: pt.Seq) -> None:
        self.accept_append_context(type_.inner, "<inner>")
        if isinstance(type_.length, pt.Int):
            self.accept_append_context(type_.length, "<length type>")

    def visit_detached_variant(self, type_: pt.DetachedVariant) -> None:
        self.accept_append_context(type_.variant, "<variant>")

    def visit_virtual(self, type_: pt.Virtual) -> None:
        self.accept_append_context(type_.inner, "<inner>")

    def visit_enum_def(self, type_: pt.EnumDef) -> None:
        self.check_root_type(type_)

    def visit_struct_def(self, type_: pt.StructDef) -> None:
        self.check_root_type(type_)

    def visit_variant_def(self, type_: pt.VariantDef) -> None:
        self.check_root_type(type_)

    def visit_hash_variant_def(self, type_: pt.HashVariantDef) -> None:
        self.check_root_type(type_)

    def visit_conversions_from_prior(self, c: pt.ConversionsFromPrior) -> None:
        prior_types = c.prior._proto_proto.defined_types
        current_types = self.current_protocol.defined_types
        known_overrides: Graph[QName, None] = Graph()
        for override in c.overrides:
            known_overrides.put(
                override.src.qualified_name(), override.target.qualified_name(), None
            )
            override.accept(self)

        for current_type_name, current_type in current_types.items():
            if current_type_name in prior_types:
                prior_type = prior_types[current_type_name]
                self.try_implicit_conversion(known_overrides, prior_type, current_type)
                self.try_implicit_conversion(known_overrides, current_type, prior_type)

    def try_implicit_conversion(
        self, known_overrides: Graph[QName, None], src: pt.RootType, target: pt.RootType
    ) -> None:
        if not known_overrides.contains(src.qualified_name(), target.qualified_name()):
            maybe_conv = src.accept_rtv(ConversionMaker(target))
            if maybe_conv is not None:
                maybe_conv.accept(self)

    def visit_conversion(self, c: pt.Conversion) -> None:
        c.accept(self)

    def check_conversion_src_target(self, conversion: pt.Conversion) -> None:
        self.check_root_type(conversion.src)
        self.check_root_type(conversion.target)

        src_qname, target_qname = (
            conversion.src.qualified_name(),
            conversion.target.qualified_name(),
        )
        if src_qname == target_qname:
            self.error(
                f"Identity conversion not permitted: {src_qname} -> {target_qname}"
            )
        elif self.conversions.contains(src_qname, target_qname):
            self.error(
                f"Multiple definitions of conversion {src_qname} -> {target_qname}"
            )
        elif (
            self.current_protocol.name != src_qname.namespace()
            and self.current_protocol.name != target_qname.namespace()
        ):
            self.error(
                f"Conversion {src_qname} -> {target_qname} may not be defined in {self.current_protocol.name}"
            )
        else:
            self.conversions.put(
                src_qname,
                target_qname,
                pt.ResolvedConversion(self.current_protocol.name, conversion),
            )

    def visit_no_conversion(self, conversion: pt.NoConversion) -> None:
        pass

    def visit_enum_conversion(self, conversion: pt.EnumConversion) -> None:
        self.check_conversion_src_target(conversion)

    def visit_struct_conversion(self, conversion: pt.StructConversion) -> None:
        self.check_conversion_src_target(conversion)

    def visit_variant_conversion(self, conversion: pt.VariantConversion) -> None:
        self.check_conversion_src_target(conversion)


@dataclasses.dataclass
class RootTypeChecker(pt.RootTypeVisitor):
    tc: TypeChecker

    def visit_enum_def(self, type_: pt.EnumDef) -> None:
        self.tc.accept_append_context(type_.underlying, "<underlying>")

        for key in type_.variants.keys():
            if not valid_identifier(key):
                self.tc.errors.append(Error(f"Invalid variant name: {key}"))

        used_values: t.Dict[int, str] = {}
        for key, value in type_.variants.items():
            if value in used_values:
                self.tc.error(
                    f"Multiple enums with same value: {key} => {value}\n"
                    f"Note: same value as: {used_values[value]}"
                )
            used_values[value] = key

    def visit_struct_def(self, type_: pt.StructDef) -> None:
        self.tc.push_context_with_name(unwrap(type_.name))

        for fname, ftype in type_.fields.items():
            if not valid_identifier(fname):
                self.tc.error(f"Invalid field name: {fname}")
            self.tc.accept_append_context(ftype, fname)

        self.tc.pop_context()

    def visit_variant_def(self, type_: pt.VariantDef) -> None:
        self.tc.accept_append_context(type_.tag_type, "<tag_type>")
        for struct in type_.variants.keys():
            self.tc.accept_append_context(struct, "<variant>")

    def visit_hash_variant_def(self, type_: pt.HashVariantDef) -> None:
        self.tc.accept_append_context(type_.tag_type, "<tag_type>")
        for struct in type_.hash_types:
            self.tc.accept_append_context(struct, "<variant>")


@dataclasses.dataclass
class ConstantTypeChecker(pt.RootConstantVisitor):
    tc: TypeChecker

    def visit_int_constant(self, constant: pt.RootIntConstant) -> None:
        # TODO - make sure the int is in-range
        pass

    def visit_string_constant(self, constant: pt.RootStringConstant) -> None:
        # Can't really mess up a string constant
        pass


@dataclasses.dataclass
class ConversionMaker(pt.RootTypeVisitor[t.Optional[pt.Conversion]]):
    target: pt.RootType

    def visit_enum_def(self, src: pt.EnumDef) -> t.Optional[pt.Conversion]:
        if not isinstance(self.target, pt.EnumDef):
            return None
        else:
            return pt.EnumConversion(src=src, target=self.target)

    def visit_struct_def(self, src: pt.StructDef) -> t.Optional[pt.Conversion]:
        if not isinstance(self.target, pt.StructDef):
            return None
        else:
            return pt.StructConversion(src=src, target=self.target)

    def visit_variant_def(self, src: pt.VariantDef) -> t.Optional[pt.Conversion]:
        if not isinstance(self.target, pt.VariantDef):
            return None
        else:
            return pt.VariantConversion(src=src, target=self.target)

    def visit_hash_variant_def(
        self, src: pt.HashVariantDef
    ) -> t.Optional[pt.Conversion]:
        return None
