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

import enum

BITS_PER_BYTE = 8


@enum.unique
class Sign(enum.Enum):
    UNSIGNED = enum.auto()
    SIGNED = enum.auto()

    def short_name(self) -> str:
        if self == Sign.SIGNED:
            return "i"
        else:
            return "u"


@enum.unique
class Endianness(enum.Enum):
    BIG = enum.auto()
    LITTLE = enum.auto()

    def __str__(self) -> str:
        return self.name

    def short_name(self) -> str:
        if self == Endianness.BIG:
            return "b"
        else:
            return "l"


def representable_range_bits(width: int, sign: Sign) -> range:
    if sign == Sign.UNSIGNED:
        # Range of an n-bit unsigned number is
        # [0, 2^n)
        return range(0, 2 ** width)
    else:
        # Range of an n-bit signed number is
        # [-2^(n - 1), 2^(n - 1))
        return range(-(2 ** (width - 1)), 2 ** (width - 1))


def representable_range(width: int, sign: Sign) -> range:
    return representable_range_bits(width * BITS_PER_BYTE, sign)
