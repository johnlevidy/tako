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
from tako.util.qname import QName


def run(types: t.Dict[QName, mir.RootType], type_order: t.List[QName]) -> t.List[Error]:
    for name in type_order:
        replacement = types[name].accept(SeqExpand())
        if replacement is not None:
            types[name] = replacement
    return []


@dataclasses.dataclass
class SeqExpand(mir.RootTypeVisitor[t.Optional[mir.Struct]]):
    def visit_struct(self, root: mir.Struct) -> t.Optional[mir.Struct]:
        new_fields: t.Dict[str, mir.Type] = {}
        for fname, ftype in root.fields.items():
            if isinstance(ftype, mir.UnboundSeq):
                new_fname = f"{fname}_injected_len_"
                new_fields[new_fname] = ftype.length_type
                new_fields[fname] = mir.Seq(
                    ftype.inner, mir.VariableLength(mir.FieldReference(new_fname))
                )
            else:
                new_fields[fname] = ftype
        return mir.Struct(root.name, new_fields)

    def visit_variant(self, root: mir.Variant) -> t.Optional[mir.Struct]:
        return None

    def visit_enum(self, root: mir.Enum) -> t.Optional[mir.Struct]:
        return None
