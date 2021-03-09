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


class External(Protocol):
    Color = Enum[lu32](
        RED=auto(),
        ORANGE=auto(),
        YELLOW=auto(),
        GREEN=auto(),
        BLUE=auto(),
        INDIGO=auto(),
        VIOLET=auto(),
    )

    String = Struct(len=li32, data=Seq(i8, this.len))
