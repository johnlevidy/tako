import typing as t
import dataclasses
from tako.core.internal_error import InternalError
import tako.core.types as pt
from tako.core.compiler.types import mir
from tako.util.qname import QName
from tako.util.cast import checked_cast

# Define a type variable that can be either pt.Type or pt.RootType
T = t.TypeVar('T', pt.Type, pt.RootType)

@dataclasses.dataclass
class ProtocolNode(t.Generic[T]):
    value: T
    children: t.List['ProtocolNode[T]']

# Specialization for only root types
@dataclasses.dataclass
class RootProtocolNode(ProtocolNode[pt.RootType]):
    pass

# Return a list of the root types. Probably want this to be a dict from def 
# to ref eventually ( TODO ) 
def build(types: t.Dict[QName, pt.RootType]) -> t.List[RootProtocolNode]:
    # TODO go through the list and dispatch all the root types
    roots = []
    for type_ in types.values():
        roots.append(type_.accept_rtv(RootProtocolGraph()))
    return roots

class RootProtocolGraph(pt.RootTypeVisitor[RootProtocolNode]):
    def visit_enum_def(self, type_: pt.EnumDef) -> RootProtocolNode:
        return RootProtocolNode(type_, [])

    def visit_struct_def(self, type_: pt.StructDef) -> RootProtocolNode:
        children = []
        for child_type in type_.fields.values():
            children.append(child_type.accept(ProtocolGraph()))

        return RootProtocolNode(type_, children)

    def visit_variant_def(self, type_: pt.VariantDef) -> RootProtocolNode:
        children = []
        for struct in type_.variants.keys():
            children.append(struct.accept(ProtocolGraph()))
        return RootProtocolNode(type_, children)

    def visit_hash_variant_def(self, type_: pt.HashVariantDef) -> RootProtocolNode:
        children = []
        for struct in type_.hash_types:
            children.append(struct.accept(ProtocolGraph()))
        return RootProtocolNode(type_, children)

class ProtocolGraph(pt.TypeVisitor[ProtocolNode[pt.Type]]):
    def visit_int(self, type_: pt.Int) -> ProtocolNode[pt.Type]:
        return ProtocolNode(type_, [])

    def visit_float(self, type_: pt.Float) -> ProtocolNode[pt.Type]:
        return ProtocolNode(type_, [])

    def visit_seq(self, type_: pt.Seq) -> ProtocolNode[pt.Type]:
        return ProtocolNode(type_, [])

    def visit_virtual(self, type_: pt.Virtual) -> ProtocolNode[pt.Type]:
        return ProtocolNode(type_, [])

    def visit_enum_def(self, type_: pt.EnumDef) -> ProtocolNode[pt.Type]:
        return ProtocolNode(type_, [])

    def visit_struct_def(self, type_: pt.StructDef) -> ProtocolNode[pt.Type]:
        children = []
        for child_type in type_.fields.values():
            children.append(child_type.accept(ProtocolGraph()))

        return ProtocolNode(type_, children)

    def visit_variant_def(self, type_: pt.VariantDef) -> ProtocolNode[pt.Type]:
        children = []
        for struct in type_.variants.keys():
            children.append(struct.accept(ProtocolGraph()))
        return ProtocolNode(type_, children)

    def visit_detached_variant(self, type_: pt.DetachedVariant) -> ProtocolNode[pt.Type]:
        children = []
        for struct in type_.variant.variants.keys():
            children.append(struct.accept(ProtocolGraph()))
        return ProtocolNode(type_, children)

    def visit_hash_variant_def(self, type_: pt.HashVariantDef) -> ProtocolNode[pt.Type]:
        children = []
        for struct in type_.hash_types:
            children.append(struct.accept(ProtocolGraph()))
        return ProtocolNode(type_, children)
