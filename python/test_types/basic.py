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
from test_types.external import External

import textwrap


class Basic(Protocol):
    MAGIC_NUMBER = Constant[li32](1492)
    MAGIC_STR = Constant[str](
        textwrap.dedent(
            """\
        This is the special magic string.
        It can even have newlines."""
        )
    )
    MAGIC_SHORT_STR = Constant[str]("pixie dust")

    Primitives = Struct(
        f_i8=i8,
        f_li16=li16,
        f_li32=li32,
        f_li64=li64,
        f_bi16=bi16,
        f_bi32=bi32,
        f_bi64=bi64,
        f_u8=u8,
        f_lu16=lu16,
        f_lu32=lu32,
        f_lu64=lu64,
        f_bu16=bu16,
        f_bu32=bu32,
        f_bu64=bu64,
        f_lf32=lf32,
        f_lf64=lf64,
        f_bf32=bf32,
        f_bf64=bf64,
    )

    Arrays = Struct(
        f_i8=Seq(i8, 3),
        f_li16=Seq(li16, 3),
        f_li32=Seq(li32, 3),
        f_li64=Seq(li64, 3),
        f_bi16=Seq(bi16, 3),
        f_bi32=Seq(bi32, 3),
        f_bi64=Seq(bi64, 3),
        f_u8=Seq(u8, 3),
        f_lu16=Seq(lu16, 3),
        f_lu32=Seq(lu32, 3),
        f_lu64=Seq(lu64, 3),
        f_bu16=Seq(bu16, 3),
        f_bu32=Seq(bu32, 3),
        f_bu64=Seq(bu64, 3),
    )

    Empty = Struct()
    EmptyEmpty = Struct(empty_1=Empty, empty_2=Empty)
    EmptyInt = Struct(empty_1=Empty, empty_2=lu64)
    IntEmpty = Struct(empty_1=lu64, empty_2=Empty)

    U8Enum = Enum[u8](THING_0=auto(), THING_1=auto(), THING_2=auto(), THING_3=auto())

    BU64Enum = Enum[bu64](
        THING_0=0, THING_1=0xFFFF, THING_2=0xFFFFFFFF, THING_3=0xFFFFFFFFFFFF
    )

    Enums = Struct(
        u8_enum=U8Enum,
        bu64_enum=BU64Enum,
        u8_enum_array=Seq(U8Enum, 3),
        bu64_enum_array=Seq(BU64Enum, 3),
    )

    Flavor = Enum[u8](VANILLA=auto(), CHOCOLATE=auto())

    CookieOrder = Struct(quantity=li32, flavor=Flavor)

    CookieOrderPair = Struct(order_1=CookieOrder, order_2=CookieOrder)

    CookieOrderList = Struct(
        number_of_orders=li32, orders=Seq(CookieOrder, this.number_of_orders)
    )

    Vector = Struct(len=bi32, data=Seq(bi32, this.len))

    VectorPair = Struct(v1=Vector, v2=Vector)

    Matrix = Struct(data=Seq(Seq(i8, 3), 3))

    VarList = Struct(rows=u8, data=Virtual(Seq(Seq(i8, 3), this.rows)))

    Person = Struct(name=External.String, age=li16)

    Box = Struct(length=li16, width=li16, height=li16)

    Pencil = Struct(lead_number=i8, color=External.Color)

    Thing = Variant[u8]({Person: 0, Box: 1, Pencil: 2})

    ThingMsg = Struct(
        thing_type=Thing.tag_type, thing=DetachedVariant(Thing, this.thing_type)
    )
    TwoThingMsg = Struct(thing1=Thing, thing2=Thing)

    VirtualThingMsg = Struct(
        thing_type=Thing.tag_type,
        thing=Virtual(DetachedVariant(Thing, this.thing_type)),
    )
