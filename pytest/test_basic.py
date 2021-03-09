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

from tako.util.cast import checked_cast

from takogen.test_types import Basic
from takogen.test_types import External

from helpers import check_parsed


class TestBasic(TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Basic.MAGIC_NUMBER, 1492)
        self.assertEqual(
            Basic.MAGIC_STR,
            "This is the special magic string.\nIt can even have newlines.",
        )
        self.assertEqual(Basic.MAGIC_SHORT_STR, "pixie dust")

    def test_primitives(self) -> None:
        # fmt: off
        data = bytes([
            # f_i8 (i8) = 0x01
            0x01,
            # f_li16 (li16) = 0x4321
            0x21, 0x43,
            # f_li32 (li32) = 0x87654321
            0x21, 0x43, 0x65, 0x87,
            # f_li64 (li64) = 0xfedcba0987654321
            0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe,
            # f_bi16 (bi16) = 0x4321
            0x43, 0x21,
            # f_bi32 (bi32) = 0x87654321
            0x87, 0x65, 0x43, 0x21,
            # f_bi64 (bi64) = 0xfedcba0987654321
            0xfe, 0xdc, 0xba, 0x09, 0x87, 0x65, 0x43, 0x21,
            # f_u8 (u8) = 0x01
            0x01,
            # f_lu16 (lu16) = 0x4321
            0x21, 0x43,
            # f_lu32 (lu32) = 0x87654321
            0x21, 0x43, 0x65, 0x87,
            # f_lu64 (lu64) = 0xfedcba0987654321
            0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe,
            # f_bu16 (bu16) = 0x4321
            0x43, 0x21,
            # f_bu32 (bu32) = 0x87654321
            0x87, 0x65, 0x43, 0x21,
            # f_bu64 (bu64) = 0xfedcba0987654321
            0xfe, 0xdc, 0xba, 0x09, 0x87, 0x65, 0x43, 0x21,
            # f_lf32 (lf32) = 0x3e200000
            # 0b00111110001000000000000000000000
            # Sign: 0 (+)
            # Exponent: 0b01111100 = 124. Biased = 124 - 127 = -3
            # Significand: 0b01000000000000000000000 = 2097152.
            # (-1)**0 * (1 + 2097152 / 2**23) * 2**-3 = 0.15625
            0x00, 0x00, 0x20, 0x3e,
            # f_lf64 (lf64) = 0x3fc4000000000000
            # 0b0011111111000100000000000000000000000000000000000000000000000000
            # Sign: 0 (+)
            # Exponent: 0b1111111100 = 1020. Biased = 1020 - 1023 = -3
            # Significand: 0100000000000000000000000000000000000000000000000000 = 1125899906842624.
            # (-1)**0 * (1 + 1125899906842624 / 2**52) * 2**-3 = 0.15625
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc4, 0x3f,
            # f_bf32 (bf32) = 0x3e200000
            0x3e, 0x20, 0x00, 0x00,
            # f_bf64 (bf64) = 0x3fc4000000000000
            0x3f, 0xc4, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.Primitives.parse(data, 0))

        self.assertEqual(parsed.f_i8, 0x01)
        self.assertEqual(parsed.f_li16, 0x4321)
        self.assertEqual(parsed.f_li32, 0x87654321 - 2 ** 32)
        self.assertEqual(parsed.f_li64, 0xFEDCBA0987654321 - 2 ** 64)
        self.assertEqual(parsed.f_bi16, 0x4321)
        self.assertEqual(parsed.f_bi32, 0x87654321 - 2 ** 32)
        self.assertEqual(parsed.f_bi64, 0xFEDCBA0987654321 - 2 ** 64)

        self.assertEqual(parsed.f_u8, 0x01)
        self.assertEqual(parsed.f_lu16, 0x4321)
        self.assertEqual(parsed.f_lu32, 0x87654321)
        self.assertEqual(parsed.f_lu64, 0xFEDCBA0987654321)
        self.assertEqual(parsed.f_bu16, 0x4321)
        self.assertEqual(parsed.f_bu32, 0x87654321)
        self.assertEqual(parsed.f_bu64, 0xFEDCBA0987654321)

        self.assertEqual(parsed.f_lf32, float.fromhex("0x1.4p-3"))
        self.assertEqual(parsed.f_lf64, float.fromhex("0x1.4p-3"))
        self.assertEqual(parsed.f_bf32, float.fromhex("0x1.4p-3"))
        self.assertEqual(parsed.f_bf64, float.fromhex("0x1.4p-3"))

        self.assertEqual(data, parsed.serialize())

    def test_arrays(self) -> None:
        # Now 3 of each thing
        # fmt: off
        data = bytes([
            # f_i8 (i8)
            0x01,
            0x02,
            0x03,
            # f_li16 (li16)
            0x21, 0x43,
            0x65, 0x87,
            0x09, 0xba,
            # f_li32 (li32)
            0x21, 0x43, 0x65, 0x87,
            0x09, 0xba, 0xdc, 0xfe,
            0x11, 0x22, 0x33, 0x44,
            # f_li64 (li64)
            0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe,
            0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
            0x99, 0x00, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff,
            # f_bi16 (bi16)
            0x43, 0x21,
            0x87, 0x65,
            0xba, 0x09,
            # f_bi32 (bi32)
            0x87, 0x65, 0x43, 0x21,
            0xfe, 0xdc, 0xba, 0x09,
            0x44, 0x33, 0x22, 0x11,
            # f_bi64 (bi64)
            0xfe, 0xdc, 0xba, 0x09, 0x87, 0x65, 0x43, 0x21,
            0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11,
            0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x00, 0x99,
            # f_u8 (u8)
            0x01,
            0x02,
            0x03,
            # f_lu16 (lu16)
            0x21, 0x43,
            0x65, 0x87,
            0x09, 0xba,
            # f_lu32 (lu32)
            0x21, 0x43, 0x65, 0x87,
            0x09, 0xba, 0xdc, 0xfe,
            0x11, 0x22, 0x33, 0x44,
            # f_lu64 (lu64)
            0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe,
            0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
            0x99, 0x00, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff,
            # f_bu16 (bu16)
            0x43, 0x21,
            0x87, 0x65,
            0xba, 0x09,
            # f_bu32 (bu32)
            0x87, 0x65, 0x43, 0x21,
            0xfe, 0xdc, 0xba, 0x09,
            0x44, 0x33, 0x22, 0x11,
            # f_bu64 (bu64)
            0xfe, 0xdc, 0xba, 0x09, 0x87, 0x65, 0x43, 0x21,
            0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11,
            0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x00, 0x99
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.Arrays.parse(data, 0))

        self.assertEqual(parsed.f_i8[0], 0x01)
        self.assertEqual(parsed.f_i8[1], 0x02)
        self.assertEqual(parsed.f_i8[2], 0x03)
        self.assertEqual(parsed.f_li16[0], 0x4321)
        self.assertEqual(parsed.f_li16[1], 0x8765 - 2 ** 16)
        self.assertEqual(parsed.f_li16[2], 0xBA09 - 2 ** 16)
        self.assertEqual(parsed.f_li32[0], 0x87654321 - 2 ** 32)
        self.assertEqual(parsed.f_li32[1], 0xFEDCBA09 - 2 ** 32)
        self.assertEqual(parsed.f_li32[2], 0x44332211)
        self.assertEqual(parsed.f_li64[0], 0xFEDCBA0987654321 - 2 ** 64)
        self.assertEqual(parsed.f_li64[1], 0x8877665544332211 - 2 ** 64)
        self.assertEqual(parsed.f_li64[2], 0xFFEEDDCCBBAA0099 - 2 ** 64)
        self.assertEqual(parsed.f_bi16[0], 0x4321)
        self.assertEqual(parsed.f_bi16[1], 0x8765 - 2 ** 16)
        self.assertEqual(parsed.f_bi16[2], 0xBA09 - 2 ** 16)
        self.assertEqual(parsed.f_bi32[0], 0x87654321 - 2 ** 32)
        self.assertEqual(parsed.f_bi32[1], 0xFEDCBA09 - 2 ** 32)
        self.assertEqual(parsed.f_bi32[2], 0x44332211)
        self.assertEqual(parsed.f_bi64[0], 0xFEDCBA0987654321 - 2 ** 64)
        self.assertEqual(parsed.f_bi64[1], 0x8877665544332211 - 2 ** 64)
        self.assertEqual(parsed.f_bi64[2], 0xFFEEDDCCBBAA0099 - 2 ** 64)

        self.assertEqual(parsed.f_u8[0], 0x01)
        self.assertEqual(parsed.f_u8[1], 0x02)
        self.assertEqual(parsed.f_u8[2], 0x03)
        self.assertEqual(parsed.f_lu16[0], 0x4321)
        self.assertEqual(parsed.f_lu16[1], 0x8765)
        self.assertEqual(parsed.f_lu16[2], 0xBA09)
        self.assertEqual(parsed.f_lu32[0], 0x87654321)
        self.assertEqual(parsed.f_lu32[1], 0xFEDCBA09)
        self.assertEqual(parsed.f_lu32[2], 0x44332211)
        self.assertEqual(parsed.f_lu64[0], 0xFEDCBA0987654321)
        self.assertEqual(parsed.f_lu64[1], 0x8877665544332211)
        self.assertEqual(parsed.f_lu64[2], 0xFFEEDDCCBBAA0099)
        self.assertEqual(parsed.f_bu16[0], 0x4321)
        self.assertEqual(parsed.f_bu16[1], 0x8765)
        self.assertEqual(parsed.f_bu16[2], 0xBA09)
        self.assertEqual(parsed.f_bu32[0], 0x87654321)
        self.assertEqual(parsed.f_bu32[1], 0xFEDCBA09)
        self.assertEqual(parsed.f_bu32[2], 0x44332211)
        self.assertEqual(parsed.f_bu64[0], 0xFEDCBA0987654321)
        self.assertEqual(parsed.f_bu64[1], 0x8877665544332211)
        self.assertEqual(parsed.f_bu64[2], 0xFFEEDDCCBBAA0099)

        self.assertEqual(data, parsed.serialize())

    def test_enums(self) -> None:
        # fmt: off
        data = bytes([
            # u8_enum (U8Enum (u8)) = U8Enum::THING_3
            0x03,
            # bu64_enum (BU64Enum (bu64)) = BU64Enum::THING_1
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff,
            # u8_enum_array (U8Enum (u8))
            0x00,
            0x01,
            0x03,
            # bu64_enum_array (BU64Enum (bu64))
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff,
            0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.Enums.parse(data, 0))

        self.assertEqual(parsed.u8_enum, Basic.U8Enum.THING_3)
        self.assertEqual(parsed.bu64_enum, Basic.BU64Enum.THING_1)
        self.assertEqual(parsed.u8_enum_array[0], Basic.U8Enum.THING_0)
        self.assertEqual(parsed.u8_enum_array[1], Basic.U8Enum.THING_1)
        self.assertEqual(parsed.u8_enum_array[2], Basic.U8Enum.THING_3)
        self.assertEqual(parsed.bu64_enum_array[0], Basic.BU64Enum.THING_0)
        self.assertEqual(parsed.bu64_enum_array[1], Basic.BU64Enum.THING_1)
        self.assertEqual(parsed.bu64_enum_array[2], Basic.BU64Enum.THING_2)

        self.assertEqual(data, parsed.serialize())

    def test_cookie_order_pair(self) -> None:
        # fmt: off
        data = bytes([
            # order_1 (CookieOrder)
            # quantity (li32) = 10,
            0x0a, 0x00, 0x00, 0x00,
            # flavor (Flavor) = VANILLA
            0x00,
            # order_2 (CookieOrder)
            # quantity (li32) = 11,
            0x0b, 0x00, 0x00, 0x00,
            # flavor (Flavor) = CHOCOLATE
            0x01
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.CookieOrderPair.parse(data, 0))

        self.assertEqual(parsed.order_1.quantity, 10)
        self.assertEqual(parsed.order_1.flavor, Basic.Flavor.VANILLA)
        self.assertEqual(parsed.order_2.quantity, 11)
        self.assertEqual(parsed.order_2.flavor, Basic.Flavor.CHOCOLATE)

        self.assertEqual(data, parsed.serialize())

    def test_cookie_order_list(self) -> None:
        # fmt: off
        data = bytes([
            # number_of_orders (li32)
            0x03, 0x00, 0x00, 0x00,
            # orders (Seq(CookieOrder, this.number_of_orders))
            # orders[0] (CookieOrder)
            # quantity (li32) = 10,
            0x0a, 0x00, 0x00, 0x00,
            # flavor (Flavor) = VANILLA
            0x00,
            # orders[1] (CookieOrder)
            # quantity (li32) = 11,
            0x0b, 0x00, 0x00, 0x00,
            # flavor (Flavor) = CHOCOLATE
            0x01,
            # orders[2] (CookieOrder)
            # quantity (li32) = 12,
            0x0c, 0x00, 0x00, 0x00,
            # flavor (Flavor) = CHOCOLATE
            0x01
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.CookieOrderList.parse(data, 0))

        self.assertEqual(len(parsed.orders), 3)
        self.assertEqual(parsed.orders[0].quantity, 10)
        self.assertEqual(parsed.orders[0].flavor, Basic.Flavor.VANILLA)
        self.assertEqual(parsed.orders[1].quantity, 11)
        self.assertEqual(parsed.orders[1].flavor, Basic.Flavor.CHOCOLATE)
        self.assertEqual(parsed.orders[2].quantity, 12)
        self.assertEqual(parsed.orders[2].flavor, Basic.Flavor.CHOCOLATE)

        self.assertEqual(data, parsed.serialize())

    def test_vector(self) -> None:
        # fmt: off
        data = bytes([
            # len (bi32)
            0x00, 0x00, 0x00, 0x03,
            # data (Seq(bi32, this.len))
            0xde, 0xad, 0xbe, 0xef,
            0xca, 0xfe, 0xba, 0xbe,
            0x00, 0xc0, 0xff, 0xee
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.Vector.parse(data, 0))

        self.assertEqual(len(parsed.data), 3)
        self.assertEqual(parsed.data[0], 0xDEADBEEF - 2 ** 32)
        self.assertEqual(parsed.data[1], 0xCAFEBABE - 2 ** 32)
        self.assertEqual(parsed.data[2], 0x00C0FFEE)

        self.assertEqual(data, parsed.serialize())

    def test_vector_pair(self) -> None:
        # fmt: off
        data = bytes([
            # v1 (Vector)
            # len (bi32)
            0x00, 0x00, 0x00, 0x03,
            # data (Seq(bi32, this.len))
            0xde, 0xad, 0xbe, 0xef,
            0xca, 0xfe, 0xba, 0xbe,
            0x00, 0xc0, 0xff, 0xee,
            # v2 (Vector)
            # len (bi32)
            0x00, 0x00, 0x00, 0x01,
            # data (Seq(bi32, this.len))
            0x11, 0x11, 0x11, 0x11
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.VectorPair.parse(data, 0))

        self.assertEqual(len(parsed.v1.data), 3)
        self.assertEqual(parsed.v1.data[0], 0xDEADBEEF - 2 ** 32)
        self.assertEqual(parsed.v1.data[1], 0xCAFEBABE - 2 ** 32)
        self.assertEqual(parsed.v1.data[2], 0x00C0FFEE)
        self.assertEqual(len(parsed.v2.data), 1)
        self.assertEqual(parsed.v2.data[0], 0x11111111)

        self.assertEqual(data, parsed.serialize())

    def test_matrix(self) -> None:
        # fmt: off
        data = bytes([
            # data = [[0x1, 0x2, 0x3], [0x4, 0x5, 0x6], [0x7, 0x8, 0x9]] ([[i8; 3]; 3])
            0x1, 0x2, 0x3,
            0x4, 0x5, 0x6,
            0x7, 0x8, 0x9
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.Matrix.parse(data, 0))

        self.assertEqual(parsed.data[0][0], 0x1)
        self.assertEqual(parsed.data[0][1], 0x2)
        self.assertEqual(parsed.data[0][2], 0x3)
        self.assertEqual(parsed.data[1][0], 0x4)
        self.assertEqual(parsed.data[1][1], 0x5)
        self.assertEqual(parsed.data[1][2], 0x6)
        self.assertEqual(parsed.data[2][0], 0x7)
        self.assertEqual(parsed.data[2][1], 0x8)
        self.assertEqual(parsed.data[2][2], 0x9)

        self.assertEqual(data, parsed.serialize())

    def test_var_matrix(self) -> None:
        # Parse the virtual field data
        # fmt: off
        data = bytes([
            # rows = 4 (u8)
            0x4,
            # data = [[0x1, 0x2, 0x3], [0x4, 0x5, 0x6], [0x7, 0x8, 0x9], [0xa, 0xb, 0xc]] ([[i8; cols]; rows])
            0x1, 0x2, 0x3,
            0x4, 0x5, 0x6,
            0x7, 0x8, 0x9,
            0xa, 0xb, 0xc
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.VarList.parse(data, 0))

        self.assertEqual(parsed.rows, 0x4)

        offset, p_data = check_parsed(parsed.data(data, offset))
        self.assertEqual(p_data[0][0], 0x1)
        self.assertEqual(p_data[0][1], 0x2)
        self.assertEqual(p_data[0][2], 0x3)
        self.assertEqual(p_data[1][0], 0x4)
        self.assertEqual(p_data[1][1], 0x5)
        self.assertEqual(p_data[1][2], 0x6)
        self.assertEqual(p_data[2][0], 0x7)
        self.assertEqual(p_data[2][1], 0x8)
        self.assertEqual(p_data[2][2], 0x9)
        self.assertEqual(p_data[3][0], 0xA)
        self.assertEqual(p_data[3][1], 0xB)
        self.assertEqual(p_data[3][2], 0xC)

    def test_person(self) -> None:
        # fmt: off
        data = bytes([
            # name (External.String)
            # len (li32)
            0x03, 0x00, 0x00, 0x00,
            # data (Seq(i8, this.len))
            98, 111, 98,
            # age (li16)
            0x04, 0x00
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.Person.parse(data, 0))

        self.assertEqual(len(parsed.name.data), 3)
        self.assertEqual(parsed.name.data[0], ord("b"))
        self.assertEqual(parsed.name.data[1], ord("o"))
        self.assertEqual(parsed.name.data[2], ord("b"))
        self.assertEqual(parsed.age, 4)

        self.assertEqual(data, parsed.serialize())

    def test_box(self) -> None:
        # fmt: off
        data = bytes([
            # length (li16)
            0x01, 0x00,
            # width (li16)
            0x02, 0x00,
            # height (li16)
            0x03, 0x00
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.Box.parse(data, 0))

        self.assertEqual(parsed.length, 1)
        self.assertEqual(parsed.width, 2)
        self.assertEqual(parsed.height, 3)

        self.assertEqual(data, parsed.serialize())

    def test_pencil(self) -> None:
        # fmt: off
        data = bytes([
            # lead_number (i8)
            0x02,
            # color (External.Color(lu32))
            0x06, 0x00, 0x00, 0x00
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.Pencil.parse(data, 0))

        self.assertEqual(parsed.lead_number, 2)
        self.assertEqual(parsed.color, External.Color.VIOLET)

        self.assertEqual(data, parsed.serialize())

    def test_thing_types(self) -> None:
        self.assertIn(Basic.Person, Basic.Thing.types)
        self.assertIn(Basic.Box, Basic.Thing.types)
        self.assertIn(Basic.Pencil, Basic.Thing.types)
        self.assertEqual(len(Basic.Thing.types), 3)

    def test_thing_person(self) -> None:
        # fmt: off
        data = bytes([
            # thing_type (Thing.tag_type(u8))
            0x00,
            # thing
            # name (External.String)
            # len (li32)
            0x03, 0x00, 0x00, 0x00,
            # data (Seq(i8, this.len))
            98, 111, 98,
            # age (li16)
            0x04, 0x00
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.ThingMsg.parse(data, 0))

        person = checked_cast(Basic.Person, parsed.thing.value)
        self.assertEqual(len(person.name.data), 3)
        self.assertEqual(person.name.data[0], ord("b"))
        self.assertEqual(person.name.data[1], ord("o"))
        self.assertEqual(person.name.data[2], ord("b"))
        self.assertEqual(person.age, 4)

        self.assertEqual(data, parsed.serialize())

    def test_thing_box(self) -> None:
        # fmt: off
        data = bytes([
            # thing_type (Thing.tag_type(u8))
            0x01,
            # thing
            # length (li16)
            0x01, 0x00,
            # width (li16)
            0x02, 0x00,
            # height (li16)
            0x03, 0x00
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.ThingMsg.parse(data, 0))

        box = checked_cast(Basic.Box, parsed.thing.value)
        self.assertEqual(box.length, 1)
        self.assertEqual(box.width, 2)
        self.assertEqual(box.height, 3)

        self.assertEqual(data, parsed.serialize())

    def test_thing_pencil(self) -> None:
        # fmt: off
        data = bytes([
            # thing_type (Thing.tag_type(u8))
            0x02,
            # thing
            # lead_number (i8)
            0x02,
            # color (External.Color(lu32))
            0x06, 0x00, 0x00, 0x00
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.ThingMsg.parse(data, 0))

        pencil = checked_cast(Basic.Pencil, parsed.thing.value)
        self.assertEqual(pencil.lead_number, 2)
        self.assertEqual(pencil.color, External.Color.VIOLET)

        self.assertEqual(data, parsed.serialize())

    def test_thing_virtual_pencil(self) -> None:
        # fmt: off
        data = bytes([
            # thing_type (Thing.tag_type(u8))
            0x02,
            # thing
            # lead_number (i8)
            0x02,
            # color (External.Color(lu32))
            0x06, 0x00, 0x00, 0x00
        ])
        # fmt: on
        offset, parsed = check_parsed(Basic.VirtualThingMsg.parse(data, 0))
        offset, thing = check_parsed(parsed.thing(data, offset))

        pencil = checked_cast(Basic.Pencil, thing.value)
        self.assertEqual(pencil.lead_number, 2)
        self.assertEqual(pencil.color, External.Color.VIOLET)

        built = bytearray(parsed.size_bytes() + thing.size_bytes())
        parsed.serialize_into(built, 0)
        thing.serialize_into(built, parsed.size_bytes())
        self.assertEqual(data, built)
