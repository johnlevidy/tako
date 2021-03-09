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
from collections import deque

V = t.TypeVar("V")
E = t.TypeVar("E")


@dataclasses.dataclass(frozen=True)
class Cycle(t.Generic[V]):
    vertices: t.Set[V]


@dataclasses.dataclass
class Graph(t.Generic[V, E]):
    graph: t.Dict[V, t.Dict[V, E]] = dataclasses.field(default_factory=dict)

    @staticmethod
    def from_iterable(things: t.Iterable[t.Tuple[V, V, E]]) -> Graph[V, E]:
        result: Graph[V, E] = Graph()
        for src, dst, value in things:
            result.put(src, dst, value)
        return result

    def contains(self, src: V, target: V) -> bool:
        # Has to be this way to handle the case were E is of type None
        empty: t.Dict[V, E] = {}
        return target in self.graph.get(src, empty)

    def get(self, src: V, target: V) -> t.Optional[E]:
        empty: t.Dict[V, E] = {}
        return self.graph.get(src, empty).get(target, None)

    def put(self, src: V, target: V, conversion: E) -> None:
        self.graph.setdefault(src, {})[target] = conversion

        # Make sure all nodes are in the primary graph
        self.graph.setdefault(target, {})

    def toposort(self) -> t.Union[t.List[V], Cycle[V]]:
        in_degrees: t.Dict[V, int] = {v: 0 for v in self.vertices()}
        for _, dst, _ in self:
            in_degrees[dst] += 1

        top_queue: t.Deque[V] = deque()
        for vertex, in_degree in in_degrees.items():
            if in_degree == 0:
                top_queue.append(vertex)
        for vertex in top_queue:
            del in_degrees[vertex]

        result: t.List[V] = []
        while in_degrees:
            if not top_queue:
                return Cycle(set(in_degrees.keys()))
            src = top_queue.popleft()
            result.append(src)
            for dst in self.graph[src]:
                in_degrees[dst] -= 1
                if in_degrees[dst] == 0:
                    top_queue.append(dst)
                    del in_degrees[dst]

        result.extend(top_queue)
        return result

    def __iter__(self) -> t.Iterator[t.Tuple[V, V, E]]:
        for src, dst_map in self.graph.items():
            for dst, value in dst_map.items():
                yield src, dst, value

    def vertices(self) -> t.Iterable[V]:
        # This is safe because every time a new node is added
        # we put it in the primary map
        return self.graph.keys()

    def edges(self) -> t.Iterator[E]:
        for _, _, edge in self:
            yield edge

    def links(self) -> t.Iterator[t.Tuple[V, V]]:
        for src, dst, _ in self:
            yield src, dst
