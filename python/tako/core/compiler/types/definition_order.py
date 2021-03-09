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
from tako.util.qname import QName
from tako.core.error import Error


def run(types: t.Dict[QName, mir.RootType], type_order: t.List[QName]) -> t.List[Error]:
    def_order = DefinitionOrder(types)
    for name in type_order:
        types[name].accept(def_order)
    return def_order.errors


@dataclasses.dataclass
class DefinitionOrder(mir.RootTypeVisitor[None], mir.SeqTypeVisitor[None]):
    types: t.Dict[QName, mir.RootType]

    defined: t.Set[QName] = dataclasses.field(default_factory=set)
    errors: t.List[Error] = dataclasses.field(default_factory=list)

    def error(self, desc: str) -> None:
        # TODO: factor out the error logging code from type_check.py
        self.errors.append(Error(desc))

    def visit_int(self, type_: mir.Int) -> None:
        pass

    def visit_float(self, type_: mir.Float) -> None:
        pass

    def visit_seq(self, type_: mir.Seq) -> None:
        type_.inner.accept(self)

    def visit_unbound_seq(self, type_: mir.UnboundSeq) -> None:
        type_.inner.accept(self)
        type_.length_type.accept(self)

    def visit_detached_variant(self, type_: mir.DetachedVariant) -> None:
        type_.variant.accept(self)

    def visit_virtual(self, type_: mir.Virtual) -> None:
        type_.inner.accept(self)

    def visit_ref(self, type_: mir.Ref) -> None:
        if type_.name not in self.defined:
            self.error(f"Type used before definition: {type_.name}")
        else:
            self.types[type_.name].accept(self)

    # Only mark the root types as defined after checking all the parts
    # Otherwise you can have a recursive type

    def visit_struct(self, root: mir.Struct) -> None:
        for ftype in root.fields.values():
            ftype.accept(self)
        self.defined.add(root.name)

    def visit_variant(self, root: mir.Variant) -> None:
        root.tag_type.accept(self)
        for type_ in root.types():
            type_.accept(self)
        self.defined.add(root.name)

    def visit_enum(self, root: mir.Enum) -> None:
        root.underlying_type.accept(self)
        self.defined.add(root.name)
