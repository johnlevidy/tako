// Copyright 2020 Jacob Glueck
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package tako;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import tako.ParseException;
import takogen.test_types.Basic;
import takogen.test_types.Basic.Primitives;
import takogen.test_types.Basic.PrimitivesView;
import takogen.test_types.Basic.Arrays;
import takogen.test_types.Basic.ArraysView;
import takogen.test_types.Basic.Enums;
import takogen.test_types.Basic.EnumsView;
import takogen.test_types.Basic.U8Enum;
import takogen.test_types.Basic.BU64Enum;
import takogen.test_types.Basic.CookieOrder;
import takogen.test_types.Basic.CookieOrderView;
import takogen.test_types.Basic.CookieOrderPair;
import takogen.test_types.Basic.CookieOrderPairView;
import takogen.test_types.Basic.CookieOrderList;
import takogen.test_types.Basic.CookieOrderListView;
import takogen.test_types.Basic.Flavor;
import takogen.test_types.Basic.Vector;
import takogen.test_types.Basic.VectorView;
import takogen.test_types.Basic.VectorPair;
import takogen.test_types.Basic.VectorPairView;
import takogen.test_types.Basic.Matrix;
import takogen.test_types.Basic.MatrixView;
import takogen.test_types.Basic.VarList;
import takogen.test_types.Basic.VarListView;
import takogen.test_types.Basic.VarListTakoContext;
import takogen.test_types.Basic.Person;
import takogen.test_types.Basic.PersonView;
import takogen.test_types.Basic.Box;
import takogen.test_types.Basic.BoxView;
import takogen.test_types.Basic.Pencil;
import takogen.test_types.Basic.PencilView;
import takogen.test_types.Basic.Thing;
import takogen.test_types.Basic.ThingView;
import takogen.test_types.Basic.ThingMsg;
import takogen.test_types.Basic.ThingMsgView;
import takogen.test_types.Basic.TwoThingMsg;
import takogen.test_types.Basic.TwoThingMsgView;
import takogen.test_types.Basic.VirtualThingMsg;
import takogen.test_types.Basic.VirtualThingMsgView;
import takogen.test_types.External.Color;
import static tako.Helpers.*;

public class TestBasic {
    @Test
    public void constants() {
        Assertions.assertEquals(Basic.MAGIC_NUMBER, 1492);
        Assertions.assertEquals(Basic.MAGIC_STR, "This is the special magic string.\nIt can even have newlines.");
        Assertions.assertEquals(Basic.MAGIC_SHORT_STR, "pixie dust");
    }

    @Test
    public void primitives() throws ParseException {
        ByteBuffer data = bytes(
            // f_i8 (i8) = 0x01
            0x01,
            // f_li16 (li16) = 0x4321
            0x21, 0x43,
            // f_li32 (li32) = 0x87654321
            0x21, 0x43, 0x65, 0x87,
            // f_li64 (li64) = 0xfedcba0987654321
            0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe,
            // f_bi16 (bi16) = 0x4321
            0x43, 0x21,
            // f_bi32 (bi32) = 0x87654321
            0x87, 0x65, 0x43, 0x21,
            // f_bi64 (bi64) = 0xfedcba0987654321
            0xfe, 0xdc, 0xba, 0x09, 0x87, 0x65, 0x43, 0x21,
            // f_u8 (u8) = 0x01
            0x01,
            // f_lu16 (lu16) = 0x4321
            0x21, 0x43,
            // f_lu32 (lu32) = 0x87654321
            0x21, 0x43, 0x65, 0x87,
            // f_lu64 (lu64) = 0xfedcba0987654321
            0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe,
            // f_bu16 (bu16) = 0x4321
            0x43, 0x21,
            // f_bu32 (bu32) = 0x87654321
            0x87, 0x65, 0x43, 0x21,
            // f_bu64 (bu64) = 0xfedcba0987654321
            0xfe, 0xdc, 0xba, 0x09, 0x87, 0x65, 0x43, 0x21,
            // f_lf32 (lf32) = 0x3e200000
            // 0b00111110001000000000000000000000
            // Sign: 0 (+)
            // Exponent: 0b01111100 = 124. Biased = 124 - 127 = -3
            // Significand: 0b01000000000000000000000 = 2097152.
            // (-1)**0 * (1 + 2097152 / 2**23) * 2**-3 = 0.15625
            0x00, 0x00, 0x20, 0x3e,
            // f_lf64 (lf64) = 0x3fc4000000000000
            // 0b0011111111000100000000000000000000000000000000000000000000000000
            // Sign: 0 (+)
            // Exponent: 0b1111111100 = 1020. Biased = 1020 - 1023 = -3
            // Significand: 0100000000000000000000000000000000000000000000000000 = 1125899906842624.
            // (-1)**0 * (1 + 1125899906842624 / 2**52) * 2**-3 = 0.15625
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc4, 0x3f,
            // f_bf32 (bf32) = 0x3e200000
            0x3e, 0x20, 0x00, 0x00,
            // f_bf64 (bf64) = 0x3fc4000000000000
            0x3f, 0xc4, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        );

        PrimitivesView parsed = new PrimitivesView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.fI8(), 0x01);
        Assertions.assertEquals(parsed.fLi16(), 0x4321);
        Assertions.assertEquals(parsed.fLi32(), 0x87654321);
        Assertions.assertEquals(parsed.fLi64(), 0xfedcba0987654321L);
        Assertions.assertEquals(parsed.fBi16(), 0x4321);
        Assertions.assertEquals(parsed.fBi32(), 0x87654321);
        Assertions.assertEquals(parsed.fBi64(), 0xfedcba0987654321L);

        Assertions.assertEquals(parsed.fU8(), 0x01);
        Assertions.assertEquals(parsed.fLu16(), 0x4321);
        Assertions.assertEquals(parsed.fLu32(), 0x87654321);
        Assertions.assertEquals(parsed.fLu64(), 0xfedcba0987654321L);
        Assertions.assertEquals(parsed.fBu16(), 0x4321);
        Assertions.assertEquals(parsed.fBu32(), 0x87654321);
        Assertions.assertEquals(parsed.fBu64(), 0xfedcba0987654321L);

        Assertions.assertEquals(parsed.fLf32(), Float.valueOf("0x1.4p-3"));
        Assertions.assertEquals(parsed.fLf64(), Double.valueOf("0x1.4p-3"));
        Assertions.assertEquals(parsed.fBf32(), Float.valueOf("0x1.4p-3"));
        Assertions.assertEquals(parsed.fBf64(), Double.valueOf("0x1.4p-3"));

        var built = new Primitives().init()
            .fI8((byte)0x01)
            .fLi16((short)0x4321)
            .fLi32(0x87654321)
            .fLi64(0xfedcba0987654321L)
            .fBi16((short)0x4321)
            .fBi32(0x87654321)
            .fBi64(0xfedcba0987654321L)
            .fU8((byte)0x01)
            .fLu16((short)0x4321)
            .fLu32(0x87654321)
            .fLu64(0xfedcba0987654321L)
            .fBu16((short)0x4321)
            .fBu32(0x87654321)
            .fBu64(0xfedcba0987654321L)
            .fLf32(Float.valueOf("0x1.4p-3"))
            .fLf64(Double.valueOf("0x1.4p-3"))
            .fBf32(Float.valueOf("0x1.4p-3"))
            .fBf64(Double.valueOf("0x1.4p-3"))
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }
    @Test
    public void arrays() throws ParseException {
        // Now 3 of each thing
        ByteBuffer data = bytes(
            // f_i8 (i8)
            0x01,
            0x02,
            0x03,
            // f_li16 (li16)
            0x21, 0x43,
            0x65, 0x87,
            0x09, 0xba,
            // f_li32 (li32)
            0x21, 0x43, 0x65, 0x87,
            0x09, 0xba, 0xdc, 0xfe,
            0x11, 0x22, 0x33, 0x44,
            // f_li64 (li64)
            0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe,
            0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
            0x99, 0x00, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff,
            // f_bi16 (bi16)
            0x43, 0x21,
            0x87, 0x65,
            0xba, 0x09,
            // f_bi32 (bi32)
            0x87, 0x65, 0x43, 0x21,
            0xfe, 0xdc, 0xba, 0x09,
            0x44, 0x33, 0x22, 0x11,
            // f_bi64 (bi64)
            0xfe, 0xdc, 0xba, 0x09, 0x87, 0x65, 0x43, 0x21,
            0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11,
            0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x00, 0x99,
            // f_u8 (u8)
            0x01,
            0x02,
            0x03,
            // f_lu16 (lu16)
            0x21, 0x43,
            0x65, 0x87,
            0x09, 0xba,
            // f_lu32 (lu32)
            0x21, 0x43, 0x65, 0x87,
            0x09, 0xba, 0xdc, 0xfe,
            0x11, 0x22, 0x33, 0x44,
            // f_lu64 (lu64)
            0x21, 0x43, 0x65, 0x87, 0x09, 0xba, 0xdc, 0xfe,
            0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
            0x99, 0x00, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff,
            // f_bu16 (bu16)
            0x43, 0x21,
            0x87, 0x65,
            0xba, 0x09,
            // f_bu32 (bu32)
            0x87, 0x65, 0x43, 0x21,
            0xfe, 0xdc, 0xba, 0x09,
            0x44, 0x33, 0x22, 0x11,
            // f_bu64 (bu64)
            0xfe, 0xdc, 0xba, 0x09, 0x87, 0x65, 0x43, 0x21,
            0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11,
            0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x00, 0x99
        );
        ArraysView parsed = new ArraysView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.fI8().get(0), (byte) 0x01);
        Assertions.assertEquals(parsed.fI8().get(1), (byte) 0x02);
        Assertions.assertEquals(parsed.fI8().get(2), (byte) 0x03);
        Assertions.assertEquals(parsed.fLi16().get(0), (short) 0x4321);
        Assertions.assertEquals(parsed.fLi16().get(1), (short) 0x8765);
        Assertions.assertEquals(parsed.fLi16().get(2), (short) 0xba09);
        Assertions.assertEquals(parsed.fLi32().get(0), 0x87654321);
        Assertions.assertEquals(parsed.fLi32().get(1), 0xfedcba09);
        Assertions.assertEquals(parsed.fLi32().get(2), 0x44332211);
        Assertions.assertEquals(parsed.fLi64().get(0), 0xfedcba0987654321L);
        Assertions.assertEquals(parsed.fLi64().get(1), 0x8877665544332211L);
        Assertions.assertEquals(parsed.fLi64().get(2), 0xffeeddccbbaa0099L);
        Assertions.assertEquals(parsed.fBi16().get(0), (short) 0x4321);
        Assertions.assertEquals(parsed.fBi16().get(1), (short) 0x8765);
        Assertions.assertEquals(parsed.fBi16().get(2), (short) 0xba09);
        Assertions.assertEquals(parsed.fBi32().get(0), 0x87654321);
        Assertions.assertEquals(parsed.fBi32().get(1), 0xfedcba09);
        Assertions.assertEquals(parsed.fBi32().get(2), 0x44332211);
        Assertions.assertEquals(parsed.fBi64().get(0), 0xfedcba0987654321L);
        Assertions.assertEquals(parsed.fBi64().get(1), 0x8877665544332211L);
        Assertions.assertEquals(parsed.fBi64().get(2), 0xffeeddccbbaa0099L);

        Assertions.assertEquals(parsed.fU8().get(0), (byte) 0x01);
        Assertions.assertEquals(parsed.fU8().get(1), (byte) 0x02);
        Assertions.assertEquals(parsed.fU8().get(2), (byte) 0x03);
        Assertions.assertEquals(parsed.fLu16().get(0), (short) 0x4321);
        Assertions.assertEquals(parsed.fLu16().get(1), (short) 0x8765);
        Assertions.assertEquals(parsed.fLu16().get(2), (short) 0xba09);
        Assertions.assertEquals(parsed.fLu32().get(0), 0x87654321);
        Assertions.assertEquals(parsed.fLu32().get(1), 0xfedcba09);
        Assertions.assertEquals(parsed.fLu32().get(2), 0x44332211);
        Assertions.assertEquals(parsed.fLu64().get(0), 0xfedcba0987654321L);
        Assertions.assertEquals(parsed.fLu64().get(1), 0x8877665544332211L);
        Assertions.assertEquals(parsed.fLu64().get(2), 0xffeeddccbbaa0099L);
        Assertions.assertEquals(parsed.fBu16().get(0), (short) 0x4321);
        Assertions.assertEquals(parsed.fBu16().get(1), (short) 0x8765);
        Assertions.assertEquals(parsed.fBu16().get(2), (short) 0xba09);
        Assertions.assertEquals(parsed.fBu32().get(0), 0x87654321);
        Assertions.assertEquals(parsed.fBu32().get(1), 0xfedcba09);
        Assertions.assertEquals(parsed.fBu32().get(2), 0x44332211);
        Assertions.assertEquals(parsed.fBu64().get(0), 0xfedcba0987654321L);
        Assertions.assertEquals(parsed.fBu64().get(1), 0x8877665544332211L);
        Assertions.assertEquals(parsed.fBu64().get(2), 0xffeeddccbbaa0099L);

        Arrays built = new Arrays().init()
            .fI8((x) -> {
                x.set(0, (byte) 0x01);
                x.set(1, (byte) 0x02);
                x.set(2, (byte) 0x03);
                return x;
            })
            .fLi16((x) -> {
                x.set(0, (short) 0x4321);
                x.set(1, (short) 0x8765);
                x.set(2, (short) 0xba09);
                return x;
            })
            .fLi32((x) -> {
                x.set(0, (int) 0x87654321);
                x.set(1, (int) 0xfedcba09);
                x.set(2, (int) 0x44332211);
                return x;
            })
            .fLi64((x) -> {
                x.set(0, (long) 0xfedcba0987654321L);
                x.set(1, (long) 0x8877665544332211L);
                x.set(2, (long) 0xffeeddccbbaa0099L);
                return x;
            })
            .fBi16((x) -> {
                x.set(0, (short) 0x4321);
                x.set(1, (short) 0x8765);
                x.set(2, (short) 0xba09);
                return x;
            })
            .fBi32((x) -> {
                x.set(0, (int) 0x87654321);
                x.set(1, (int) 0xfedcba09);
                x.set(2, (int) 0x44332211);
                return x;
            })
            .fBi64((x) -> {
                x.set(0, (long) 0xfedcba0987654321L);
                x.set(1, (long) 0x8877665544332211L);
                x.set(2, (long) 0xffeeddccbbaa0099L);
                return x;
            })
            .fU8((x) -> {
                x.set(0, (byte) 0x01);
                x.set(1, (byte) 0x02);
                x.set(2, (byte) 0x03);
                return x;
            })
            .fLu16((x) -> {
                x.set(0, (short) 0x4321);
                x.set(1, (short) 0x8765);
                x.set(2, (short) 0xba09);
                return x;
            })
            .fLu32((x) -> {
                x.set(0, (int) 0x87654321);
                x.set(1, (int) 0xfedcba09);
                x.set(2, (int) 0x44332211);
                return x;
            })
            .fLu64((x) -> {
                x.set(0, (long) 0xfedcba0987654321L);
                x.set(1, (long) 0x8877665544332211L);
                x.set(2, (long) 0xffeeddccbbaa0099L);
                return x;
            })
            .fBu16((x) -> {
                x.set(0, (short) 0x4321);
                x.set(1, (short) 0x8765);
                x.set(2, (short) 0xba09);
                return x;
            })
            .fBu32((x) -> {
                x.set(0, (int) 0x87654321);
                x.set(1, (int) 0xfedcba09);
                x.set(2, (int) 0x44332211);
                return x;
            })
            .fBu64((x) -> {
                x.set(0, (long) 0xfedcba0987654321L);
                x.set(1, (long) 0x8877665544332211L);
                x.set(2, (long) 0xffeeddccbbaa0099L);
                return x;
            })
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void enums() throws ParseException {
        ByteBuffer data = bytes(
            // u8_enum (U8Enum (u8)) = U8Enum::THING_3
            0x03,
            // bu64_enum (BU64Enum (bu64)) = BU64Enum::THING_1
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff,
            // u8_enum_array (U8Enum (u8))
            0x00,
            0x01,
            0x03,
            // bu64_enum_array (BU64Enum (bu64))
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff,
            0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff
        );
        EnumsView parsed = new EnumsView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.u8Enum(), U8Enum.THING_3);
        Assertions.assertEquals(parsed.bu64Enum(), BU64Enum.THING_1);
        Assertions.assertEquals(parsed.u8EnumArray().get(0), U8Enum.THING_0);
        Assertions.assertEquals(parsed.u8EnumArray().get(1), U8Enum.THING_1);
        Assertions.assertEquals(parsed.u8EnumArray().get(2), U8Enum.THING_3);
        Assertions.assertEquals(parsed.bu64EnumArray().get(0), BU64Enum.THING_0);
        Assertions.assertEquals(parsed.bu64EnumArray().get(1), BU64Enum.THING_1);
        Assertions.assertEquals(parsed.bu64EnumArray().get(2), BU64Enum.THING_2);

        Enums built = new Enums().init()
            .u8Enum(U8Enum.THING_3)
            .bu64Enum(BU64Enum.THING_1)
            .u8EnumArray((x) -> {
                x.set(0, U8Enum.THING_0);
                x.set(1, U8Enum.THING_1);
                x.set(2, U8Enum.THING_3);
                return x;
            })
            .bu64EnumArray((x) -> {
                x.set(0, BU64Enum.THING_0);
                x.set(1, BU64Enum.THING_1);
                x.set(2, BU64Enum.THING_2);
                return x;
            })
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void cookieOrderPair() throws ParseException {
        ByteBuffer data = bytes(
            // order_1 (CookieOrder)
            // quantity (li32) = 10,
            0x0a, 0x00, 0x00, 0x00,
            // flavor (Flavor) = VANILLA
            0x00,
            // order_2 (CookieOrder)
            // quantity (li32) = 11,
            0x0b, 0x00, 0x00, 0x00,
            // flavor (Flavor) = CHOCOLATE
            0x01
        );
        CookieOrderPairView parsed = new CookieOrderPairView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.order1().quantity(), 10);
        Assertions.assertEquals(parsed.order1().flavor(), Flavor.VANILLA);
        Assertions.assertEquals(parsed.order2().quantity(), 11);
        Assertions.assertEquals(parsed.order2().flavor(), Flavor.CHOCOLATE);

        CookieOrderPair built = new CookieOrderPair();
        built.init()
            .order1().enter()
                .quantity(10)
                .flavor(Flavor.VANILLA)
                .finish()
            .order2().enter()
                .quantity(11)
                .flavor(Flavor.CHOCOLATE)
                .finish()
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void cookieOrderList() throws ParseException {
        ByteBuffer data = bytes(
            // number_of_orders (li32)
            0x03, 0x00, 0x00, 0x00,
            // orders (Seq(CookieOrder, this.number_of_orders))
            // orders[0] (CookieOrder)
            // quantity (li32) = 10,
            0x0a, 0x00, 0x00, 0x00,
            // flavor (Flavor) = VANILLA
            0x00,
            // orders[1] (CookieOrder)
            // quantity (li32) = 11,
            0x0b, 0x00, 0x00, 0x00,
            // flavor (Flavor) = CHOCOLATE
            0x01,
            // orders[2] (CookieOrder)
            // quantity (li32) = 12,
            0x0c, 0x00, 0x00, 0x00,
            // flavor (Flavor) = CHOCOLATE
            0x01
        );
        CookieOrderListView parsed = new CookieOrderListView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.numberOfOrders(), 3);
        Assertions.assertEquals(parsed.orders().get(0).quantity(), 10);
        Assertions.assertEquals(parsed.orders().get(0).flavor(), Flavor.VANILLA);
        Assertions.assertEquals(parsed.orders().get(1).quantity(), 11);
        Assertions.assertEquals(parsed.orders().get(1).flavor(), Flavor.CHOCOLATE);
        Assertions.assertEquals(parsed.orders().get(2).quantity(), 12);
        Assertions.assertEquals(parsed.orders().get(2).flavor(), Flavor.CHOCOLATE);

        CookieOrderList built = new CookieOrderList().init()
            .orders((x) -> {
                x.add(new CookieOrder().init().quantity(10).flavor(Flavor.VANILLA).finish());
                x.add(new CookieOrder().init().quantity(11).flavor(Flavor.CHOCOLATE).finish());
                x.add(new CookieOrder().init().quantity(12).flavor(Flavor.CHOCOLATE).finish());
                return x;
            })
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void vectorPair() throws ParseException {
        ByteBuffer data = bytes(
            // v1 (Vector)
            // len (bi32)
            0x00, 0x00, 0x00, 0x03,
            // data (Seq(bi32, this.len))
            0xde, 0xad, 0xbe, 0xef,
            0xca, 0xfe, 0xba, 0xbe,
            0x00, 0xc0, 0xff, 0xee,
            // v2 (Vector)
            // len (bi32)
            0x00, 0x00, 0x00, 0x01,
            // data (Seq(bi32, this.len))
            0x11, 0x11, 0x11, 0x11
        );
        VectorPairView parsed = new VectorPairView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.v1().len(), 3);
        Assertions.assertEquals(parsed.v1().data().get(0), 0xdeadbeef);
        Assertions.assertEquals(parsed.v1().data().get(1), 0xcafebabe);
        Assertions.assertEquals(parsed.v1().data().get(2), 0x00c0ffee);
        Assertions.assertEquals(parsed.v2().len(), 1);
        Assertions.assertEquals(parsed.v2().data().get(0), 0x11111111);

        VectorPair built = new VectorPair().init()
            .v1().enter()
                .data((x) -> {
                    x.add(0xdeadbeef);
                    x.add(0xcafebabe);
                    x.add(0x00c0ffee);
                    return x;
                })
                .finish()
            .v2().enter()
                .data((x) -> {
                    x.add(0x11111111);
                    return x;
                })
                .finish()
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void matrix() throws ParseException {
        ByteBuffer data = bytes(
            // data = [[0x1, 0x2, 0x3], [0x4, 0x5, 0x6], [0x7, 0x8, 0x9]] ([[i8; 3]; 3])
            0x1, 0x2, 0x3,
            0x4, 0x5, 0x6,
            0x7, 0x8, 0x9
        );
        MatrixView parsed = new MatrixView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.data().get(0).get(0), 0x1);
        Assertions.assertEquals(parsed.data().get(0).get(1), 0x2);
        Assertions.assertEquals(parsed.data().get(0).get(2), 0x3);
        Assertions.assertEquals(parsed.data().get(1).get(0), 0x4);
        Assertions.assertEquals(parsed.data().get(1).get(1), 0x5);
        Assertions.assertEquals(parsed.data().get(1).get(2), 0x6);
        Assertions.assertEquals(parsed.data().get(2).get(0), 0x7);
        Assertions.assertEquals(parsed.data().get(2).get(1), 0x8);
        Assertions.assertEquals(parsed.data().get(2).get(2), 0x9);

        Matrix built = new Matrix().init()
            .data((x) -> {
                x.get(0).set(0, (byte) 0x1);
                x.get(0).set(1, (byte) 0x2);
                x.get(0).set(2, (byte) 0x3);
                x.get(1).set(0, (byte) 0x4);
                x.get(1).set(1, (byte) 0x5);
                x.get(1).set(2, (byte) 0x6);
                x.get(2).set(0, (byte) 0x7);
                x.get(2).set(1, (byte) 0x8);
                x.get(2).set(2, (byte) 0x9);
                return x;
            })
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void varMatrix() throws ParseException {
        ByteBuffer data = bytes(
            // rows = 4 (u8)
            0x4,
            // data = [[0x1, 0x2, 0x3], [0x4, 0x5, 0x6], [0x7, 0x8, 0x9], [0xa, 0xb, 0xc]] ([[i8; 3]; rows])
            0x1, 0x2, 0x3,
            0x4, 0x5, 0x6,
            0x7, 0x8, 0x9,
            0xa, 0xb, 0xc
        );
        VarListView parsed = new VarListView();
        int offset = parsed.parse(data, 0);

        var virtualData = VarListTakoContext.data.newRendered();
        parsed.data(virtualData, data, offset);
        Assertions.assertEquals(virtualData.get(0).get(0), 0x1);
        Assertions.assertEquals(virtualData.get(0).get(1), 0x2);
        Assertions.assertEquals(virtualData.get(0).get(2), 0x3);
        Assertions.assertEquals(virtualData.get(1).get(0), 0x4);
        Assertions.assertEquals(virtualData.get(1).get(1), 0x5);
        Assertions.assertEquals(virtualData.get(1).get(2), 0x6);
        Assertions.assertEquals(virtualData.get(2).get(0), 0x7);
        Assertions.assertEquals(virtualData.get(2).get(1), 0x8);
        Assertions.assertEquals(virtualData.get(2).get(2), 0x9);
        Assertions.assertEquals(virtualData.get(3).get(0), 0xa);
        Assertions.assertEquals(virtualData.get(3).get(1), 0xb);
        Assertions.assertEquals(virtualData.get(3).get(2), 0xc);
    }

    @Test
    public void person() throws ParseException {
        ByteBuffer data = bytes(
            // name (External.String)
            // len (li32)
            0x03, 0x00, 0x00, 0x00,
            // data (Seq(i8, this.len))
            98, 111, 98,
            // age (li16)
            0x04, 0x00
        );
        PersonView parsed = new PersonView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.name().len(), 3);
        Assertions.assertEquals(parsed.name().data().get(0), 'b');
        Assertions.assertEquals(parsed.name().data().get(1), 'o');
        Assertions.assertEquals(parsed.name().data().get(2), 'b');
        Assertions.assertEquals(parsed.age(), 4);

        Person built = new Person().init()
            .name().enter()
                .data((x) -> {
                    x.add((byte) 'b');
                    x.add((byte) 'o');
                    x.add((byte) 'b');
                    return x;
                })
                .finish()
            .age((short) 4)
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void box() throws ParseException {
        ByteBuffer data = bytes(
            // length (li16)
            0x01, 0x00,
            // width (li16)
            0x02, 0x00,
            // height (li16)
            0x03, 0x00
        );
        BoxView parsed = new BoxView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.length(), 1);
        Assertions.assertEquals(parsed.width(), 2);
        Assertions.assertEquals(parsed.height(), 3);

        var built = new Box().init()
            .length((short) 1)
            .width((short) 2)
            .height((short) 3)
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void pencil() throws ParseException {
        ByteBuffer data = bytes(
            // lead_number (i8)
            0x02,
            // color (External.Color(lu32))
            0x06, 0x00, 0x00, 0x00
        );
        PencilView parsed = new PencilView();
        parsed.parse(data, 0);

        Assertions.assertEquals(parsed.leadNumber(), 2);
        Assertions.assertEquals(parsed.color(), Color.VIOLET);

        var built = new Pencil().init()
            .leadNumber((byte) 2)
            .color(Color.VIOLET)
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void thingPerson() throws ParseException {
        ByteBuffer data = bytes(
            // thing_type (Thing.tag_type(u8))
            0x00,
            // thing
            // name (External.String)
            // len (li32)
            0x03, 0x00, 0x00, 0x00,
            // data (Seq(i8, this.len))
            98, 111, 98,
            // age (li16)
            0x04, 0x00
        );
        ThingMsgView parsed = new ThingMsgView();
        parsed.parse(data, 0);

        PersonView person = parsed.thing().get(PersonView.class);
        Assertions.assertEquals(person.name().len(), 3);
        Assertions.assertEquals(person.name().data().get(0), 'b');
        Assertions.assertEquals(person.name().data().get(1), 'o');
        Assertions.assertEquals(person.name().data().get(2), 'b');
        Assertions.assertEquals(person.age(), 4);

        ThingMsg built = new ThingMsg().init()
            .thing().enter()
                .set(Person.marker).enter()
                    .name().enter()
                        .data((x) -> {
                            x.add((byte) 'b');
                            x.add((byte) 'o');
                            x.add((byte) 'b');
                            return x;
                        })
                        .finish()
                    .age((short) 4)
                    .finish()
                .finish()
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void thingBox() throws ParseException {
        ByteBuffer data = bytes(
            // thing_type (Thing.tag_type(u8))
            0x01,
            // thing
            // length (li16)
            0x01, 0x00,
            // width (li16)
            0x02, 0x00,
            // height (li16)
            0x03, 0x00
        );
        ThingMsgView parsed = new ThingMsgView();
        parsed.parse(data, 0);

        BoxView box = parsed.thing().get(BoxView.class);
        Assertions.assertNotNull(box);
        Assertions.assertEquals(box.length(), 1);
        Assertions.assertEquals(box.width(), 2);
        Assertions.assertEquals(box.height(), 3);

        ThingMsg built = new ThingMsg().init()
            .thing().enter()
                .set(Box.marker).enter()
                    .length((short) 1)
                    .width((short) 2)
                    .height((short) 3)
                    .finish()
                .finish()
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void thingPencil() throws ParseException {
        ByteBuffer data = bytes(
            // thing_type (Thing.tag_type(u8))
            0x02,
            // thing
            // lead_number (i8)
            0x02,
            // color (External.Color(lu32))
            0x06, 0x00, 0x00, 0x00
        );
        ThingMsgView parsed = new ThingMsgView();
        parsed.parse(data, 0);

        PencilView pencil = parsed.thing().get(PencilView.class);
        Assertions.assertNotNull(pencil);
        Assertions.assertEquals(pencil.leadNumber(), 2);
        Assertions.assertEquals(pencil.color(), Color.VIOLET);

        ThingMsg built = new ThingMsg().init()
            .thing().enter()
                .set(Pencil.marker).enter()
                    .leadNumber((byte) 2)
                    .color(Color.VIOLET)
                    .finish()
                .finish()
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void twoThingPencil() throws ParseException {
        ByteBuffer data = bytes(
            // thing_type (Thing.tag_type(u8))
            0x02,
            // thing
            // lead_number (i8)
            0x02,
            // color (External.Color(lu32))
            0x06, 0x00, 0x00, 0x00,
            // thing_type (Thing.tag_type(u8))
            0x02,
            // thing
            // lead_number (i8)
            0x01,
            // color (External.Color(lu32))
            0x06, 0x00, 0x00, 0x00
        );
        TwoThingMsgView parsed = new TwoThingMsgView();
        parsed.parse(data, 0);

        PencilView pencil1 = parsed.thing1().get(PencilView.class);
        Assertions.assertNotNull(pencil1);
        Assertions.assertEquals(pencil1.leadNumber(), 2);
        Assertions.assertEquals(pencil1.color(), Color.VIOLET);
        PencilView pencil2 = parsed.thing2().get(PencilView.class);
        Assertions.assertNotNull(pencil2);
        Assertions.assertEquals(pencil2.leadNumber(), 1);
        Assertions.assertEquals(pencil2.color(), Color.VIOLET);

        TwoThingMsg built = new TwoThingMsg().init()
            .thing1().enter()
                .set(Pencil.marker).enter()
                    .leadNumber((byte) 2)
                    .color(Color.VIOLET)
                    .finish()
                .finish()
            .thing2().enter()
                .set(Pencil.marker).enter()
                    .leadNumber((byte) 1)
                    .color(Color.VIOLET)
                    .finish()
                .finish()
            .finish();
        Assertions.assertTrue(bufEquals(data, built.serialize()));
    }

    @Test
    public void thingVirtualPencil() throws ParseException {
        ByteBuffer data = bytes(
            // thing_type (Thing.tag_type(u8))
            0x02,
            // thing
            // lead_number (i8)
            0x02,
            // color (External.Color(lu32))
            0x06, 0x00, 0x00, 0x00
        );
        VirtualThingMsgView parsed = new VirtualThingMsgView();
        int offset = parsed.parse(data, 0);

        ThingView thing = new ThingView();
        parsed.thing(thing, data, offset);
        PencilView pencil = thing.get(PencilView.class);
        Assertions.assertNotNull(pencil);
        Assertions.assertEquals(pencil.leadNumber(), 2);
        Assertions.assertEquals(pencil.color(), Color.VIOLET);

        VirtualThingMsg built = new VirtualThingMsg().init().thingType((byte) 2).finish();
        var builtPencil = new Pencil().init()
            .leadNumber((byte) 2)
            .color(Color.VIOLET)
            .finish();
        ByteBuffer out = ByteBuffer.allocate(built.sizeBytes() + builtPencil.sizeBytes());
        offset = built.serializeInto(out, 0);
        builtPencil.serializeInto(out, offset);
        Assertions.assertTrue(bufEquals(data, out));
    }
}
