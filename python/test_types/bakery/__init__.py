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

from .v1 import V1
from .v2 import V2
from .v3 import V3
from .v4 import V4


class Bakery(Protocol):
    PacketVariant = HashVariant[lu32]([V1.Message, V2.Message, V3.Message, V4.Message])

    Packet = Struct(payload=PacketVariant)
