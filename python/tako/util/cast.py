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

T = t.TypeVar("T")


def unwrap(x: t.Optional[T]) -> T:
    if x is None:
        raise ValueError("Unwrapped a None value")
    else:
        return x


def checked_cast(target: t.Type[T], x: t.Any) -> T:
    if x is None or not isinstance(x, target):
        raise ValueError(f"Cast failed: target: {target} src: {type(x)}")
    else:
        return x


def assert_never(x: t.Any) -> t.NoReturn:
    # Apparently this works in mypy 0.740
    # https://github.com/python/mypy/issues/6366#issuecomment-560369716
    # So for now make it t.Any, but eventually fix it
    assert False, f"Unhandled type: {x}"
