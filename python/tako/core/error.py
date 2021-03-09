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
import inspect
from tako.util.qname import QName


@dataclasses.dataclass
class Error:
    desc: str
    context: t.Optional[QName] = None
    source_type: t.Optional[t.Any] = None

    def __str__(self) -> str:
        result = ""
        if self.source_type is not None:
            code, line_number = inspect.getsourcelines(self.source_type)
            fname = inspect.getfile(self.source_type)
            result += f"[{fname}:{line_number}]: "
        if self.context is not None:
            result += f"{self.context}: "
        result += self.desc

        return result
