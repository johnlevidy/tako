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


class Conversions(Protocol):
    FlavorOld = Enum[u8](VANILLA=auto(), CHOCOLATE=auto())
    FlavorNew = Enum[u8](VANILLA=auto(), CHOCOLATE=auto(), CARMEL=auto())

    CupcakeOrderOld = Struct(flavor=FlavorOld)
    CupcakeOrderNew = Struct(flavor=FlavorNew, quantity=lu32)

    CakeOrderOld = Struct(flavor=FlavorOld)
    CakeOrderNew = Struct(flavor=FlavorNew)

    OrderOld = Variant[u8]({CakeOrderOld: 0, CupcakeOrderOld: 1})
    OrderNew = Variant[u8]({CakeOrderNew: 0, CupcakeOrderNew: 1})

    MsgOld = Struct(msg=OrderOld)
    MsgNew = Struct(msg=OrderNew)

    conversions = [
        EnumConversion(src=FlavorOld, target=FlavorNew),
        EnumConversion(
            src=FlavorNew,
            target=FlavorOld,
            mapping={FlavorNew.CARMEL: FlavorOld.CHOCOLATE},
        ),
        StructConversion(
            src=CupcakeOrderOld,
            target=CupcakeOrderNew,
            mapping={CupcakeOrderNew.quantity: 50},
        ),
        StructConversion(src=CupcakeOrderNew, target=CupcakeOrderOld),
        StructConversion(src=CakeOrderNew, target=CakeOrderOld),
        StructConversion(src=CakeOrderOld, target=CakeOrderNew),
        VariantConversion(src=OrderOld, target=OrderNew),
        VariantConversion(src=OrderNew, target=OrderOld),
        StructConversion(src=MsgNew, target=MsgOld),
        StructConversion(src=MsgOld, target=MsgNew),
    ]
