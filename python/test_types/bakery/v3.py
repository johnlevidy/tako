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
from test_types.bakery.v2 import V2 as Prior


class V3(Protocol):
    # I'm really bad at this whole bakery thing, I didn't even have carmel
    Flavor = Enum[u8](VANILLA=auto(), CHOCOLATE=auto(), CARMEL=auto())
    Shape = Enum[u8](ROUND=auto(), SQAURE=auto())

    CupcakeOrder = Struct(
        quantity=li32,
        flavor=Flavor,
        # Frosting flavor is actually the most important
        # I can't believe I forgot it
        frosting_flavor=Flavor,
    )
    CakeOrder = Struct(layers=li32, shape=Shape, flavor=Flavor)
    Order = Variant[u8]({CupcakeOrder: 0, CakeOrder: 1})

    ErrorResponse = Struct()
    NewOrderRequest = Struct(name_len=u8, name=Seq(i8, this.name_len), order=Order)
    NewOrderResponse = Struct(order_id=lu64)

    MessageVariant = Variant[u8](
        {ErrorResponse: 0, NewOrderRequest: 1, NewOrderResponse: 2}
    )
    Message = Struct(msg=MessageVariant)

    conversions = [
        ConversionsFromPrior(
            Prior,
            EnumConversion(
                src=Flavor,
                target=Prior.Flavor,
                mapping={Flavor.CARMEL: Prior.Flavor.CHOCOLATE},
            ),
        )
    ]
