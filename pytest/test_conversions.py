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

from unittest import TestCase

from takogen.test_types.Conversions import *


class TestConversions(TestCase):
    def test_conversions_flavor_old_to_flavor_new(self) -> None:
        old = FlavorOld.CHOCOLATE
        new_ = convert(old, ToFlavorNew)
        self.assertEqual(new_, FlavorNew.CHOCOLATE)

    def test_conversions_flavor_new_to_flavor_old(self) -> None:
        new_ = FlavorNew.CARMEL
        old = convert(new_, ToFlavorOld)
        self.assertEqual(old, FlavorOld.CHOCOLATE)

    def test_conversions_cupcake_order_old_to_cupcacke_order_new(self) -> None:
        old = CupcakeOrderOld(flavor=FlavorOld.CHOCOLATE)
        new_ = convert(old, ToCupcakeOrderNew)
        self.assertEqual(new_, CupcakeOrderNew(flavor=FlavorNew.CHOCOLATE, quantity=50))

    def test_conversions_cupcake_order_new_to_cupcacke_order_old(self) -> None:
        new_ = CupcakeOrderNew(flavor=FlavorNew.CARMEL, quantity=50)
        old = convert(new_, ToCupcakeOrderOld)
        self.assertEqual(old, CupcakeOrderOld(flavor=FlavorOld.CHOCOLATE))

    def test_conversions_order_old_to_order_new(self) -> None:
        old = OrderOld(CupcakeOrderOld(flavor=FlavorOld.CHOCOLATE))
        new_ = convert(old, ToOrderNew)
        self.assertEqual(
            new_, OrderNew(CupcakeOrderNew(flavor=FlavorNew.CHOCOLATE, quantity=50))
        )

    def test_conversions_order_new_to_order_old(self) -> None:
        new_ = OrderNew(CupcakeOrderNew(flavor=FlavorNew.CARMEL, quantity=50))
        old = convert(new_, ToOrderOld)
        self.assertEqual(old, OrderOld(CupcakeOrderOld(flavor=FlavorOld.CHOCOLATE)))

    def test_conversions_msg_old_to_msg_new(self) -> None:
        old = MsgOld(OrderOld(CupcakeOrderOld(flavor=FlavorOld.CHOCOLATE)))
        new_ = convert(old, ToMsgNew)
        self.assertEqual(
            new_,
            MsgNew(OrderNew(CupcakeOrderNew(flavor=FlavorNew.CHOCOLATE, quantity=50))),
        )

    def test_conversions_msg_new_to_msg_old(self) -> None:
        new_ = MsgNew(OrderNew(CupcakeOrderNew(flavor=FlavorNew.CARMEL, quantity=50)))
        old = convert(new_, ToMsgOld)
        self.assertEqual(
            old, MsgOld(OrderOld(CupcakeOrderOld(flavor=FlavorOld.CHOCOLATE)))
        )
