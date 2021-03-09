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
import typing_extensions as te
import abc
import dataclasses
import copy
from tako.util.cast import unwrap, checked_cast
from tako.util.qname import QName
from tako.util.int_model import Sign, Endianness
from tako.util.graph import Graph
from tako.util.name_format import snake_to_pascal
from tako.core.internal_error import InternalError, QuirkAbstractDataclass

# Note that a lot of this relies on the order-preserving nature of kwargs and dicts:
# * https://docs.python.org/3.7/whatsnew/3.7.html ->
#   "the insertion-order preservation nature of dict objects has been declared to be an official part of the Python language spec."
# * https://docs.python.org/3.6/whatsnew/3.6.html#pep-468-preserving-keyword-argument-order

# A subset of the Path and Path2 classes from Construct
# https://github.com/construct/construct/blob/master/construct/expr.py
# Only allows field access, unlike Construct with permits arbitrary expressions
@dataclasses.dataclass(frozen=True)
class StructPath:
    name: str


@dataclasses.dataclass(frozen=True)
class This:
    def __getattr__(self, name: str) -> StructPath:
        return StructPath(name)


this = This()

T = t.TypeVar("T")


class RootTypeVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_enum_def(self, type_: EnumDef) -> T:
        ...

    @abc.abstractmethod
    def visit_struct_def(self, type_: StructDef) -> T:
        ...

    @abc.abstractmethod
    def visit_variant_def(self, type_: VariantDef) -> T:
        ...

    @abc.abstractmethod
    def visit_hash_variant_def(self, type_: HashVariantDef) -> T:
        ...


class TypeVisitor(RootTypeVisitor[T], t.Generic[T]):
    @abc.abstractmethod
    def visit_int(self, type_: Int) -> T:
        ...

    @abc.abstractmethod
    def visit_float(self, type_: Float) -> T:
        ...

    @abc.abstractmethod
    def visit_seq(self, type_: Seq) -> T:
        ...

    @abc.abstractmethod
    def visit_detached_variant(self, type_: DetachedVariant) -> T:
        ...

    @abc.abstractmethod
    def visit_virtual(self, type_: Virtual) -> T:
        ...


class Type:
    def accept(self, visitor: TypeVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


@dataclasses.dataclass(eq=False)
class RootType(Type):
    name: t.Optional[str] = dataclasses.field(default=None, init=False)
    proto_proto: t.Optional[ProtoProto] = dataclasses.field(default=None, init=False)

    def bind_name(self, name: str) -> None:
        self.name = name

    def bind_protocol(self, proto_proto: ProtoProto) -> None:
        self.proto_proto = proto_proto

    def qualified_name(self) -> QName:
        return unwrap(self.proto_proto).name.with_name(unwrap(self.name))

    def accept_rtv(self, visitor: RootTypeVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


@dataclasses.dataclass(eq=False)
class Int(Type):
    # in bytes
    width: int
    sign: Sign
    endianness: Endianness

    def __str__(self) -> str:
        return f"{self.endianness.short_name()}{self.sign.short_name()}{self.width}"

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_int(self)


@dataclasses.dataclass(eq=False)
class Float(Type):
    # in bytes
    width: int
    endianness: Endianness

    def __str__(self) -> str:
        return f"{self.endianness.short_name()}f{self.width}"

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_float(self)


class EnumAuto:
    pass


@dataclasses.dataclass(frozen=True)
class EnumValue:
    name: str
    value: int
    src: EnumDef


@dataclasses.dataclass(eq=False)
class EnumDef(RootType):
    underlying: Int
    variants: t.Dict[str, int]

    # __getattr__ is only called if the attr can't be found normally
    # So we use it to get the enum value
    def __getattr__(self, name: str) -> EnumValue:
        if name == "__setstate__" or name not in self.variants:
            raise AttributeError(name)
        else:
            return EnumValue(name, self.variants[name], self)

    # If an enum variant has a name equal to a field of this class,
    # they can use this instead of getattr.
    def __getitem__(self, name: str) -> int:
        return self.variants[name]

    def valid_value(self, value: int) -> bool:
        return value in self.variants.values()

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_enum_def(self)

    def accept_rtv(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_enum_def(self)


class MakeEnumProtocol(te.Protocol):
    def __call__(self, **kwargs: t.Union[int, EnumAuto]) -> EnumDef:
        ...


class EnumHelper:
    def __getitem__(self, underlying: Int) -> MakeEnumProtocol:
        def make_enum(**kwargs: t.Union[int, EnumAuto]) -> EnumDef:
            assigned_variants: t.Dict[str, int] = {}
            used_values: t.Set[int] = set()
            for name, value in kwargs.items():
                if isinstance(value, EnumAuto):
                    value = 0 if not used_values else max(used_values) + 1
                assigned_variants[name] = value
                used_values.add(value)
            return EnumDef(underlying, assigned_variants)

        return make_enum


Enum = EnumHelper()


def auto() -> EnumAuto:
    return EnumAuto()


@dataclasses.dataclass(frozen=True)
class FieldReference:
    name: str
    src: StructDef


@dataclasses.dataclass(eq=False)
class StructDef(RootType):
    fields: t.Dict[str, Type]

    # __getattr__ is only called if the attr can't be found normally
    # So we use it to get the enum value
    def __getattr__(self, name: str) -> FieldReference:
        # Prevents infinite recursion on deepcopy
        if name == "__setstate__" or name not in self.fields:
            raise AttributeError(name)
        else:
            return FieldReference(name, self)

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_struct_def(self)

    def accept_rtv(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_struct_def(self)

    def duplicate(self) -> StructDef:
        return StructDef(dict(self.fields))


def Struct(**kwargs: Type) -> StructDef:  # noqa N802
    return StructDef(kwargs)


@dataclasses.dataclass(eq=False)
class VariantDef(RootType):
    tag_type: Int
    variants: t.Dict[StructDef, int]

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_variant_def(self)

    def accept_rtv(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_variant_def(self)


class VariantHelper:
    def __getitem__(
        self, tag_type: Int
    ) -> t.Callable[[t.Dict[StructDef, int]], VariantDef]:
        def make_variant(variants: t.Dict[StructDef, int]) -> VariantDef:
            return VariantDef(tag_type, variants)

        return make_variant


Variant = VariantHelper()


@dataclasses.dataclass(eq=False)
class HashVariantDef(RootType):
    tag_type: Int
    hash_types: t.List[StructDef]

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_hash_variant_def(self)

    def accept_rtv(self, visitor: RootTypeVisitor[T]) -> T:
        return visitor.visit_hash_variant_def(self)


class HashVariantHelper:
    def __getitem__(
        self, tag_type: Int
    ) -> t.Callable[[t.List[StructDef]], HashVariantDef]:
        def make_hash_variant(hash_types: t.List[StructDef]) -> HashVariantDef:
            return HashVariantDef(tag_type, hash_types)

        return make_hash_variant


HashVariant = HashVariantHelper()


@dataclasses.dataclass(eq=False)
class Seq(Type):
    inner: Type
    length: t.Union[int, StructPath, Int]

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_seq(self)


@dataclasses.dataclass(eq=False)
class DetachedVariant(Type):
    variant: VariantDef
    tag: StructPath

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_detached_variant(self)


@dataclasses.dataclass(eq=False)
class Virtual(Type):
    inner: Type

    def accept(self, visitor: TypeVisitor[T]) -> T:
        return visitor.visit_virtual(self)


class RootConstantVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_int_constant(self, constant: RootIntConstant) -> T:
        ...

    @abc.abstractmethod
    def visit_string_constant(self, constant: RootStringConstant) -> T:
        ...


@dataclasses.dataclass(eq=False)
class RootConstant:
    name: t.Optional[str] = dataclasses.field(default=None, init=False)
    proto_proto: t.Optional[ProtoProto] = dataclasses.field(default=None, init=False)

    def bind_name(self, name: str) -> None:
        self.name = name

    def bind_protocol(self, proto_proto: ProtoProto) -> None:
        self.proto_proto = proto_proto

    def qualified_name(self) -> QName:
        return unwrap(self.proto_proto).name.with_name(unwrap(self.name))

    def accept(self, visitor: RootConstantVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


@dataclasses.dataclass(eq=False)
class RootStringConstant(RootConstant):
    value: str

    def accept(self, visitor: RootConstantVisitor[T]) -> T:
        return visitor.visit_string_constant(self)


@dataclasses.dataclass(eq=False)
class RootIntConstant(RootConstant):
    type_: Int
    value: int

    def accept(self, visitor: RootConstantVisitor[T]) -> T:
        return visitor.visit_int_constant(self)


class ConstantHelper:
    @t.overload
    def __getitem__(self, type_: Int) -> t.Callable[[int], RootIntConstant]:
        ...

    @t.overload
    def __getitem__(self, type_: t.Type[str]) -> t.Callable[[str], RootStringConstant]:
        ...

    def __getitem__(
        self, type_: t.Union[Int, t.Type[str]]
    ) -> t.Union[
        t.Callable[[int], RootIntConstant], t.Callable[[str], RootStringConstant]
    ]:
        if isinstance(type_, Int):
            # MyPy has trouble with applying type restrictions to inner functions
            int_type: Int = type_

            def make_int_constant(value: int) -> RootIntConstant:
                return RootIntConstant(int_type, value)

            return make_int_constant
        else:

            def make_string_constant(value: str) -> RootStringConstant:
                return RootStringConstant(value)

            return make_string_constant


Constant = ConstantHelper()

K = t.TypeVar("K")
V = t.TypeVar("V")


def add_item(dct: t.Dict[K, V], key: K, value: V) -> None:
    if key in dct:
        raise InternalError(f"Key already present: {key} -- old value: {dct[key]}")
    dct[key] = value


@dataclasses.dataclass(eq=False)
class ExtensionContext:
    generated_types: t.Dict[str, RootType] = dataclasses.field(default_factory=dict)

    def add_type(self, name: str, type_: RootType) -> RootType:
        add_item(self.generated_types, name, type_)
        type_.bind_name(name)
        return type_

    def add_extension(self, name: str, ext: Extension) -> t.Optional[RootType]:
        ext.bind(name, self)
        return self.generated_types.get(name, None)

    @t.overload
    def add(self, name: str, value: RootType) -> RootType:
        ...

    @t.overload
    def add(self, name: str, value: Extension) -> t.Optional[RootType]:
        ...

    def add(
        self, name: str, value: t.Union[RootType, Extension]
    ) -> t.Union[RootType, t.Optional[RootType]]:
        if isinstance(value, RootType):
            return self.add_type(name, value)
        else:
            return self.add_extension(name, value)


class Extension(abc.ABC):
    @abc.abstractmethod
    def bind(self, name: str, ctxt: ExtensionContext) -> None:
        ...


class ConversionSpecifierVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_conversions_from_prior(self, c: ConversionsFromPrior) -> T:
        ...

    @abc.abstractmethod
    def visit_conversion(self, c: Conversion) -> T:
        ...


@dataclasses.dataclass(eq=False)
class ConversionSpecifier:
    def accept_cs(self, visitor: ConversionSpecifierVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


@dataclasses.dataclass(eq=False)
class ConversionsFromPrior(ConversionSpecifier):
    prior: t.Type[Protocol]
    overrides: t.List[Conversion]

    def __init__(self, prior: t.Type[Protocol], *overrides: Conversion) -> None:
        self.prior = prior
        self.overrides = list(overrides)

    def accept_cs(self, visitor: ConversionSpecifierVisitor[T]) -> T:
        return visitor.visit_conversions_from_prior(self)


class ConversionVisitor(abc.ABC, t.Generic[T]):
    @abc.abstractmethod
    def visit_no_conversion(self, type_: NoConversion) -> T:
        ...

    @abc.abstractmethod
    def visit_enum_conversion(self, type_: EnumConversion) -> T:
        ...

    @abc.abstractmethod
    def visit_struct_conversion(self, type_: StructConversion) -> T:
        ...

    @abc.abstractmethod
    def visit_variant_conversion(self, type_: VariantConversion) -> T:
        ...


@dataclasses.dataclass(eq=False)
class Conversion(ConversionSpecifier):
    src: RootType
    target: RootType

    def accept_cs(self, visitor: ConversionSpecifierVisitor[T]) -> T:
        return visitor.visit_conversion(self)

    def accept(self, visitor: ConversionVisitor[T]) -> T:
        raise QuirkAbstractDataclass()


@dataclasses.dataclass(eq=False)
class NoConversion(Conversion):
    def accept(self, visitor: ConversionVisitor[T]) -> T:
        return visitor.visit_no_conversion(self)


@dataclasses.dataclass(eq=False)
class EnumConversion(Conversion):
    src: EnumDef
    target: EnumDef
    # An entry mapping[a] = b means that for an enum value of a
    # in the source, put an enum value of b in the target.
    # If there is no mapping for a variant of the source enum, then
    # it remains unchanged in the target.
    # For example, consider e1 = {DOG: 0, CAT: 1} and e2 = {DOG: 0, CAT: 1, TIGER: 2}.
    # A mapping from e1 -> e2 could be {} -- do nothing.
    # A mapping from e2 -> e1 could be {TIGER: CAT}.
    # For this mapping to be succeed, map(x) for all x in the source enum
    # must result in a name in the target enum.
    mapping: t.Dict[EnumValue, t.Optional[EnumValue]] = dataclasses.field(
        default_factory=dict
    )

    def accept(self, visitor: ConversionVisitor[T]) -> T:
        return visitor.visit_enum_conversion(self)


@dataclasses.dataclass(eq=False)
class StructConversion(Conversion):
    src: StructDef
    target: StructDef
    # A struct conversion from struct s1 to s2 works as follows:
    # 1. Any field present in s2 with name x and in defaults integral type (enum or number) is assigned using the
    #    defaults dictionary below. Note that a field can exist in s1 and in the defaults dictionary;
    #    in this case the defaults dictionary takes precedece.
    # 2. Any field with a name x in s2 is copied from target_to_src_rename[x] (if it exists) in s1,
    #    though potentially converted to the correct type, if such a conversion exists.
    #    Again, note that this occurs even if a field with name x is in s1 -- this allows you to
    #    rename and replace a field.
    # 3. Any field with the same name in s1 and s2 is copied to s2, though potentially
    #    converted to the correct type, if such a conversion exists.
    # This mapping is invalid if there is a field in s2 which can't be set using the rules above.
    # A valid mapping may or may not be total.
    mapping: t.Dict[
        FieldReference, t.Union[EnumValue, int, FieldReference]
    ] = dataclasses.field(default_factory=dict)

    def accept(self, visitor: ConversionVisitor[T]) -> T:
        return visitor.visit_struct_conversion(self)


@dataclasses.dataclass(eq=False)
class VariantConversion(Conversion):
    src: VariantDef
    target: VariantDef
    mapping: t.Dict[StructDef, t.Optional[StructDef]] = dataclasses.field(
        default_factory=dict
    )

    def accept(self, visitor: ConversionVisitor[T]) -> T:
        return visitor.visit_variant_conversion(self)


@dataclasses.dataclass(eq=False)
class ResolvedConversion:
    protocol: QName
    inner: Conversion


@dataclasses.dataclass(eq=False)
class Option:
    pass


@dataclasses.dataclass(eq=False)
class Namespace(Option):
    namespace: QName

    @staticmethod
    def from_str(x: str) -> Namespace:
        return Namespace(QName.from_pyname(x))


@dataclasses.dataclass(eq=False)
class KeepModuleName(Option):
    pass


OptionType = t.TypeVar("OptionType", bound=Option)


@dataclasses.dataclass(eq=False)
class ProtoDict(dict):
    defined_types: t.Dict[str, RootType]
    defined_constants: t.Dict[str, RootConstant]
    conversions: t.List[ConversionSpecifier]
    options: t.List[Option]

    definition_source: t.Optional[t.Any]

    def __init__(self, **kwargs: t.Any) -> None:
        self.defined_types = {}
        self.defined_constants = {}
        self.conversions = []
        self.options = []

        self.definition_source = None

        for name, value in kwargs.items():
            self[name] = value

    def add_root(
        self, name: str, value: t.Union[t.List[Conversion], RootType, RootConstant]
    ) -> None:
        if isinstance(value, RootType):
            add_item(self.defined_types, name, value)
            value.bind_name(name)
        elif isinstance(value, RootConstant):
            add_item(self.defined_constants, name, value)
            value.bind_name(name)
        else:
            raise InternalError("Type error")

    def __setitem__(self, key: str, value: t.Any) -> None:
        if key == "conversions":
            assert isinstance(value, list)
            for v in value:
                self.conversions.append(checked_cast(ConversionSpecifier, v))
        elif key == "options":
            assert isinstance(value, list)
            for v in value:
                self.options.append(checked_cast(Option, v))
        else:
            if isinstance(value, Extension):
                ctxt = ExtensionContext()
                value.bind(key, ctxt)
                for gkey, gvalue in ctxt.generated_types.items():
                    self.add_root(gkey, gvalue)
            elif isinstance(value, RootConstant) or isinstance(value, RootType):
                self.add_root(key, value)

            super().__setitem__(key, value)

    def find_option(self, otype: t.Type[OptionType]) -> t.Optional[OptionType]:
        for option in self.options:
            if isinstance(option, otype):
                return option
        return None


@dataclasses.dataclass
class ProtoProto:
    name: QName
    defined_types: t.Dict[str, RootType]
    defined_constants: t.Dict[str, RootConstant]
    defined_conversions: t.List[ConversionSpecifier]
    definition_source: t.Optional[t.Any]

    @staticmethod
    def from_proto_dict(
        name: QName,
        proto_dict: ProtoDict,
        definition_source: t.Optional[t.Type[Protocol]] = None,
    ) -> ProtoProto:
        result = ProtoProto(
            name=name,
            defined_types=proto_dict.defined_types,
            defined_constants=proto_dict.defined_constants,
            defined_conversions=proto_dict.conversions,
            definition_source=definition_source,
        )

        for type_ in result.defined_types.values():
            type_.bind_protocol(result)
        for constant in result.defined_constants.values():
            constant.bind_protocol(result)

        return result

    def as_dict(self) -> t.Dict[str, t.Any]:
        return copy.deepcopy(
            {
                **self.defined_types,
                **self.defined_constants,
                "conversions": self.defined_conversions,
                "options": [Namespace(self.name.namespace())],
            }
        )


class ProtocolMeta(type):
    @classmethod
    def __prepare__(
        cls, __name: str, __bases: t.Tuple[t.Type, ...], **kwargs: t.Any
    ) -> t.Mapping[str, t.Any]:
        return ProtoDict()

    def __new__(
        cls, name: str, bases: t.Tuple[t.Type, ...], proto_dict: ProtoDict
    ) -> type:
        # Note the dict(proto_dict) -- this replaces
        # the proto dictionary with a normal dictionary so the defined
        # types and constants are fixed
        result: t.Type[Protocol] = type.__new__(
            cls, name, bases, t.cast(t.Dict[str, t.Any], dict(proto_dict))
        )
        # If this class happens to be the Protocol class declared below, stop,
        # don't do any of this. It's not a real protocol.
        if result.__module__ == "tako.core.types" and name == "Protocol":
            return result

        namespace_option = proto_dict.find_option(Namespace)
        if namespace_option is not None:
            proto_namespace = namespace_option.namespace
        else:
            proto_namespace = QName.from_pyname(result.__module__)
            if proto_dict.find_option(KeepModuleName) is None:
                expected = snake_to_pascal(proto_namespace.name())
                if expected != name:
                    raise ValueError(
                        f"Protocol name does not match module name: expected {expected}; found {proto_namespace.name()}"
                    )
                # Drop the last element of the name space which is now redudant with the name of the protocol itself
                proto_namespace = proto_namespace.namespace()

        result._proto_proto = ProtoProto.from_proto_dict(
            proto_namespace.with_name(result.__name__),
            proto_dict,
            proto_dict.definition_source or result,
        )
        return result


class Protocol(metaclass=ProtocolMeta):
    _proto_proto: t.ClassVar[ProtoProto]

    @classmethod
    def as_dict(cls) -> t.Dict[str, t.Any]:
        return cls._proto_proto.as_dict()


# Actually returns t.Type[Protocol]
# But the result is not usefull for type-checking in any way
# So use Any so that mypy does not try to type-check it.
def protogen(gen: t.Callable[[], t.Dict[str, t.Any]]) -> t.Any:
    proto_dict = ProtoDict(**gen())
    if proto_dict.find_option(Namespace) is None:
        proto_dict.options.append(Namespace.from_str(gen.__module__))
    proto_dict.definition_source = gen
    result = type(snake_to_pascal(gen.__name__), (Protocol,), proto_dict)
    result.__module__ = gen.__module__
    return result


@dataclasses.dataclass(eq=False)
class ProtocolDef:
    name: QName
    types: t.Dict[QName, RootType]
    # These types are sorted such that the dependencies
    # of any type appear before it
    type_order: t.List[QName]
    constants: t.Dict[QName, RootConstant]
    conversions: Graph[QName, ResolvedConversion]


i8 = Int(1, Sign.SIGNED, Endianness.LITTLE)
li16 = Int(2, Sign.SIGNED, Endianness.LITTLE)
li32 = Int(4, Sign.SIGNED, Endianness.LITTLE)
li64 = Int(8, Sign.SIGNED, Endianness.LITTLE)
bi16 = Int(2, Sign.SIGNED, Endianness.BIG)
bi32 = Int(4, Sign.SIGNED, Endianness.BIG)
bi64 = Int(8, Sign.SIGNED, Endianness.BIG)

u8 = Int(1, Sign.UNSIGNED, Endianness.LITTLE)
lu16 = Int(2, Sign.UNSIGNED, Endianness.LITTLE)
lu32 = Int(4, Sign.UNSIGNED, Endianness.LITTLE)
lu64 = Int(8, Sign.UNSIGNED, Endianness.LITTLE)
bu16 = Int(2, Sign.UNSIGNED, Endianness.BIG)
bu32 = Int(4, Sign.UNSIGNED, Endianness.BIG)
bu64 = Int(8, Sign.UNSIGNED, Endianness.BIG)

lf32 = Float(4, Endianness.LITTLE)
lf64 = Float(8, Endianness.LITTLE)
bf32 = Float(4, Endianness.BIG)
bf64 = Float(8, Endianness.BIG)

i16 = li16
i32 = li32
i64 = li64
u16 = lu16
u32 = lu32
u64 = lu64
f32 = lf32
f64 = lf64
