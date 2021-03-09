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


class RobotCmd(Protocol):
    Direction = Enum[i8](FORWARDS=auto(), BACKWARDS=auto())

    RotateDirection = Enum[i8](LEFT_90=auto(), RIGHT_90=auto())

    MoveCmd = Struct(
        direction=Direction,
        # in meters
        distance=li32,
    )

    RotateCmd = Struct(direction=RotateDirection)

    BaseCmdVariant = Variant[u8]({MoveCmd: 0, RotateCmd: 1})

    BaseCmd = Struct(cmd=BaseCmdVariant)

    CmdSeq = Struct(length=li32, cmds=Seq(BaseCmd, this.length))

    CmdVariant = Variant[u8]({MoveCmd: 0, RotateCmd: 1, CmdSeq: 2})

    Msg = Struct(cmd=CmdVariant)
