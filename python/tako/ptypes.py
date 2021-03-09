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

def make_string(ltype: Int, dtype: Int) -> StructDef:
    return Struct(len=ltype, data=Seq(dtype, this.len))

class Ptypes(Protocol):
    I8 = Struct(value=i8)
    Li16 = Struct(value=li16)
    Li32 = Struct(value=li32)
    Li64 = Struct(value=li64)
    Bi16 = Struct(value=bi16)
    Bi32 = Struct(value=bi32)
    Bi64 = Struct(value=bi64)

    U8 = Struct(value=u8)
    Lu16 = Struct(value=lu16)
    Lu32 = Struct(value=lu32)
    Lu64 = Struct(value=lu64)
    Bu16 = Struct(value=bu16)
    Bu32 = Struct(value=bu32)
    Bu64 = Struct(value=bu64)

    Empty = Struct()

    StringL8 = make_string(u8, i8)
    StringL16 = make_string(lu16, i8)
    StringL32 = make_string(lu32, i8)

    BytesL8 = make_string(u8, u8)
    BytesL16 = make_string(lu16, u8)
    BytesL32 = make_string(lu32, u8)

def make_optional(struct: StructDef) -> VariantDef:
    return Variant[u8]({Ptypes.Empty: 0, struct: 1})
