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


@dataclasses.dataclass(frozen=True)
class QName:
    parts: t.Tuple[str, ...]

    def __format__(self, spec: str) -> str:
        return str(self)

    def __str__(self) -> str:
        return ".".join(self.parts)

    def __len__(self) -> int:
        return len(self.parts)

    def name(self) -> str:
        return self.parts[-1]

    def namespace(self) -> QName:
        return QName(self.parts[:-1])

    def append(self, other: QName) -> QName:
        return QName(self.parts + other.parts)

    def prefix(self, other: QName) -> QName:
        return other.append(self)

    def with_name(self, other: str) -> QName:
        return QName(self.parts + (other,))

    def replace_name(self, new_name: str) -> QName:
        return QName(self.namespace().parts + (new_name,))

    def prefix_name(self, name_prefix: str) -> QName:
        return self.replace_name(name_prefix + self.name())

    def suffix_name(self, name_suffix: str) -> QName:
        return self.replace_name(self.name() + name_suffix)

    def apply_to_name(self, func: t.Callable[[str], str]) -> QName:
        return self.replace_name(func(self.name()))

    @staticmethod
    def from_iterable(parts: t.Iterable[str]) -> QName:
        return QName(tuple(parts))

    @staticmethod
    def from_pyname(name: str) -> QName:
        if name:
            return QName.from_iterable(name.split("."))
        else:
            return QName(())

    @staticmethod
    def from_class(cls: t.Type) -> QName:
        return QName.from_pyname(f"{cls.__module__}.{cls.__name__}")
