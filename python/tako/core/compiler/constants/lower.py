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
from tako.core.compiler import types
from tako.core.compiler.constants import lir
import tako.core.types as pt
import tako.core.size_types as st
from tako.util.qname import QName


def lower(constants: t.Dict[QName, pt.RootConstant]) -> t.Dict[QName, lir.RootConstant]:
    return {name: constant.accept(RootLower()) for name, constant in constants.items()}


@dataclasses.dataclass
class RootLower(pt.RootConstantVisitor[lir.RootConstant]):
    def visit_int_constant(self, constant: pt.RootIntConstant) -> lir.RootConstant:
        return lir.RootIntConstant(
            constant.qualified_name(),
            types.lir.Int(
                size=st.Constant(constant.type_.width),
                trivial=True,
                width=constant.type_.width,
                sign=constant.type_.sign,
                endianness=constant.type_.endianness,
            ),
            constant.value,
        )

    def visit_string_constant(
        self, constant: pt.RootStringConstant
    ) -> lir.RootConstant:
        return lir.RootStringConstant(constant.qualified_name(), constant.value)
