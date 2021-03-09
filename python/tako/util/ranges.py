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
from dataclasses import replace

T = t.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class Range:
    "Represents the inclusive range [start, end]"

    start: int
    end: int

    def is_unit(self) -> bool:
        return self.end == self.start


def find_ranges(nums: t.List[int]) -> t.List[Range]:
    snums = sorted(nums)
    result: t.List[Range] = []
    if not snums:
        return result
    current = Range(snums[0], snums[0])
    for value in snums[1:]:
        if current.end + 1 == value:
            current = replace(current, end=value)
        else:
            result.append(current)
            current = Range(value, value)
    result.append(current)
    return result
