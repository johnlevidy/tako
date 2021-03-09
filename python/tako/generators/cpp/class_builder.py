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
from tako.generators.cpp import cpp_gen as cg


@dataclasses.dataclass
class ClassBuilder:
    public: t.List[cg.Node] = dataclasses.field(default_factory=list)
    private: t.List[cg.Node] = dataclasses.field(default_factory=list)

    def add_parts(self, parts: ClassParts) -> None:
        if parts.public is not None:
            self.public.append(parts.public)
        if parts.private is not None:
            self.private.append(parts.private)

    def finalize(self) -> t.List[t.Tuple[cg.Visibility, cg.Section]]:
        return [
            (cg.Visibility.PUBLIC, cg.Section(self.public)),
            (cg.Visibility.PRIVATE, cg.Section(self.private)),
        ]


@dataclasses.dataclass
class ClassParts:
    public: t.Optional[cg.Node] = None
    private: t.Optional[cg.Node] = None
