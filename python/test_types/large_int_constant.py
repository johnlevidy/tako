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

from tako.core.types import *


def signed_min(bits: int) -> int:
    return -2 ** (bits - 1)


def signed_max(bits: int) -> int:
    return 2 ** (bits - 1) - 1


def unsigned_min(bits: int) -> int:
    return 0


def unsigned_max(bits: int) -> int:
    return 2 ** bits - 1


class LargeIntConstant(Protocol):
    C_I8_MIN = Constant[i8](signed_min(8))
    C_I8_MAX = Constant[i8](signed_max(8))
    C_LI16_MIN = Constant[li16](signed_min(16))
    C_LI16_MAX = Constant[li16](signed_max(16))
    C_LI32_MIN = Constant[li32](signed_min(32))
    C_LI32_MAX = Constant[li32](signed_max(32))
    C_LI64_MIN = Constant[li64](signed_min(64))
    C_LI64_MAX = Constant[li64](signed_max(64))
    C_BI16_MIN = Constant[bi16](signed_min(16))
    C_BI16_MAX = Constant[bi16](signed_max(16))
    C_BI32_MIN = Constant[bi32](signed_min(32))
    C_BI32_MAX = Constant[bi32](signed_max(32))
    C_BI64_MIN = Constant[bi64](signed_min(64))
    C_BI64_MAX = Constant[bi64](signed_max(64))

    C_U8_MIN = Constant[u8](unsigned_min(8))
    C_U8_MAX = Constant[u8](unsigned_max(8))
    C_LU16_MIN = Constant[lu16](unsigned_min(16))
    C_LU16_MAX = Constant[lu16](unsigned_max(16))
    C_LU32_MIN = Constant[lu32](unsigned_min(32))
    C_LU32_MAX = Constant[lu32](unsigned_max(32))
    C_LU64_MIN = Constant[lu64](unsigned_min(64))
    C_LU64_MAX = Constant[lu64](unsigned_max(64))
    C_BU16_MIN = Constant[bu16](unsigned_min(16))
    C_BU16_MAX = Constant[bu16](unsigned_max(16))
    C_BU32_MIN = Constant[bu32](unsigned_min(32))
    C_BU32_MAX = Constant[bu32](unsigned_max(32))
    C_BU64_MIN = Constant[bu64](unsigned_min(64))
    C_BU64_MAX = Constant[bu64](unsigned_max(64))
