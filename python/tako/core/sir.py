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

# Struct Intermediate Representation (SIR)
from __future__ import annotations

import dataclasses
from tako.core.compiler import types, constants, conversions
from tako.util.qname import QName

tir = types.lir
kir = constants.lir
cir = conversions.lir


@dataclasses.dataclass(frozen=True)
class Protocol:
    name: QName
    types: tir.ProtocolTypes
    constants: kir.ProtocolConstants
    conversions: cir.ProtocolConversions
