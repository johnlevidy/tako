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

#include "catch2/catch.hpp"
#include "tako/helpers.hh"
#include "test_types/basic.hh"
#include <iostream>
#include <type_traits>

using namespace test_types::basic;
using namespace test_types::external;
using namespace std;

TEST_CASE("constants") {
    STATIC_REQUIRE(MAGIC_NUMBER == 1492);
    tako::require_same<decltype(MAGIC_NUMBER), int32_t>();
    CHECK(MAGIC_STR == std::string("This is the special magic string.\nIt can even have newlines."));
    CHECK(MAGIC_SHORT_STR == std::string("pixie dust"));
}

TEST_CASE("primitives") {
    auto data = tako::byte_array(
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
    auto parsed = tako::expect_parse<PrimitivesView>(data);

    CHECK(parsed.f_i8() == 0x01);
    tako::require_same<decltype(parsed.f_i8()), int8_t>();
    CHECK(parsed.f_li16() == 0x4321);
    tako::require_same<decltype(parsed.f_li16()), int16_t>();
    CHECK(parsed.f_li32() == 0x87654321);
    tako::require_same<decltype(parsed.f_li32()), int32_t>();
    CHECK(parsed.f_li64() == 0xfedcba0987654321);
    tako::require_same<decltype(parsed.f_li64()), int64_t>();
    CHECK(parsed.f_bi16() == 0x4321);
    tako::require_same<decltype(parsed.f_bi16()), int16_t>();
    CHECK(parsed.f_bi32() == 0x87654321);
    tako::require_same<decltype(parsed.f_bi32()), int32_t>();
    CHECK(parsed.f_bi64() == 0xfedcba0987654321);
    tako::require_same<decltype(parsed.f_bi64()), int64_t>();

    CHECK(parsed.f_u8() == 0x01);
    tako::require_same<decltype(parsed.f_u8()), uint8_t>();
    CHECK(parsed.f_lu16() == 0x4321);
    tako::require_same<decltype(parsed.f_lu16()), uint16_t>();
    CHECK(parsed.f_lu32() == 0x87654321);
    tako::require_same<decltype(parsed.f_lu32()), uint32_t>();
    CHECK(parsed.f_lu64() == 0xfedcba0987654321);
    tako::require_same<decltype(parsed.f_lu64()), uint64_t>();
    CHECK(parsed.f_bu16() == 0x4321);
    tako::require_same<decltype(parsed.f_bu16()), uint16_t>();
    CHECK(parsed.f_bu32() == 0x87654321);
    tako::require_same<decltype(parsed.f_bu32()), uint32_t>();
    CHECK(parsed.f_bu64() == 0xfedcba0987654321);
    tako::require_same<decltype(parsed.f_bu64()), uint64_t>();

    CHECK(parsed.f_lf32() == 0x1.4p-3);
    tako::require_same<decltype(parsed.f_lf32()), float>();
    CHECK(parsed.f_lf64() == 0x1.4p-3);
    tako::require_same<decltype(parsed.f_lf64()), double>();
    CHECK(parsed.f_bf32() == 0x1.4p-3);
    tako::require_same<decltype(parsed.f_bf32()), float>();
    CHECK(parsed.f_bf64() == 0x1.4p-3);
    tako::require_same<decltype(parsed.f_bf64()), double>();

    Primitives owned {
        .f_i8 = 0x01,
        .f_li16 = 0x4321,
        .f_li32 = static_cast<int32_t>(0x87654321),
        .f_li64 = static_cast<int64_t>(0xfedcba0987654321),
        .f_bi16 = 0x4321,
        .f_bi32 = static_cast<int32_t>(0x87654321),
        .f_bi64 = static_cast<int64_t>(0xfedcba0987654321),
        .f_u8 = 0x01,
        .f_lu16 = 0x4321,
        .f_lu32 = 0x87654321,
        .f_lu64 = 0xfedcba0987654321,
        .f_bu16 = 0x4321,
        .f_bu32 = 0x87654321,
        .f_bu64 = 0xfedcba0987654321,
        .f_lf32 = 0x1.4p-3,
        .f_lf64 = 0x1.4p-3,
        .f_bf32 = 0x1.4p-3,
        .f_bf64 = 0x1.4p-3,
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("arrays") {
    // Now 3 of each thing
    auto data = tako::byte_array(
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
    auto parsed = tako::expect_parse<ArraysView>(data);

    CHECK(parsed.f_i8()[0] == 0x01);
    CHECK(parsed.f_i8()[1] == 0x02);
    CHECK(parsed.f_i8()[2] == 0x03);
    tako::require_same<decltype(parsed.f_i8()[0]), int8_t>();
    CHECK(parsed.f_li16()[0] == static_cast<int16_t>(0x4321));
    CHECK(parsed.f_li16()[1] == static_cast<int16_t>(0x8765));
    CHECK(parsed.f_li16()[2] == static_cast<int16_t>(0xba09));
    tako::require_same<decltype(parsed.f_li16()[0]), int16_t>();
    CHECK(parsed.f_li32()[0] == 0x87654321);
    CHECK(parsed.f_li32()[1] == 0xfedcba09);
    CHECK(parsed.f_li32()[2] == 0x44332211);
    tako::require_same<decltype(parsed.f_li32()[0]), int32_t>();
    CHECK(parsed.f_li64()[0] == 0xfedcba0987654321);
    CHECK(parsed.f_li64()[1] == 0x8877665544332211);
    CHECK(parsed.f_li64()[2] == 0xffeeddccbbaa0099);
    tako::require_same<decltype(parsed.f_li64()[0]), int64_t>();
    CHECK(parsed.f_bi16()[0] == static_cast<int16_t>(0x4321));
    CHECK(parsed.f_bi16()[1] == static_cast<int16_t>(0x8765));
    CHECK(parsed.f_bi16()[2] == static_cast<int16_t>(0xba09));
    tako::require_same<decltype(parsed.f_bi16()[0]), int16_t>();
    CHECK(parsed.f_bi32()[0] == 0x87654321);
    CHECK(parsed.f_bi32()[1] == 0xfedcba09);
    CHECK(parsed.f_bi32()[2] == 0x44332211);
    tako::require_same<decltype(parsed.f_bi32()[0]), int32_t>();
    CHECK(parsed.f_bi64()[0] == 0xfedcba0987654321);
    CHECK(parsed.f_bi64()[1] == 0x8877665544332211);
    CHECK(parsed.f_bi64()[2] == 0xffeeddccbbaa0099);
    tako::require_same<decltype(parsed.f_bi64()[0]), int64_t>();

    CHECK(parsed.f_u8()[0] == 0x01);
    CHECK(parsed.f_u8()[1] == 0x02);
    CHECK(parsed.f_u8()[2] == 0x03);
    tako::require_same<decltype(parsed.f_u8()[0]), uint8_t>();
    CHECK(parsed.f_lu16()[0] == 0x4321);
    CHECK(parsed.f_lu16()[1] == 0x8765);
    CHECK(parsed.f_lu16()[2] == 0xba09);
    tako::require_same<decltype(parsed.f_lu16()[0]), uint16_t>();
    CHECK(parsed.f_lu32()[0] == 0x87654321);
    CHECK(parsed.f_lu32()[1] == 0xfedcba09);
    CHECK(parsed.f_lu32()[2] == 0x44332211);
    tako::require_same<decltype(parsed.f_lu32()[0]), uint32_t>();
    CHECK(parsed.f_lu64()[0] == 0xfedcba0987654321);
    CHECK(parsed.f_lu64()[1] == 0x8877665544332211);
    CHECK(parsed.f_lu64()[2] == 0xffeeddccbbaa0099);
    tako::require_same<decltype(parsed.f_lu64()[0]), uint64_t>();
    CHECK(parsed.f_bu16()[0] == 0x4321);
    CHECK(parsed.f_bu16()[1] == 0x8765);
    CHECK(parsed.f_bu16()[2] == 0xba09);
    tako::require_same<decltype(parsed.f_bu16()[0]), uint16_t>();
    CHECK(parsed.f_bu32()[0] == 0x87654321);
    CHECK(parsed.f_bu32()[1] == 0xfedcba09);
    CHECK(parsed.f_bu32()[2] == 0x44332211);
    tako::require_same<decltype(parsed.f_bu32()[0]), uint32_t>();
    CHECK(parsed.f_bu64()[0] == 0xfedcba0987654321);
    CHECK(parsed.f_bu64()[1] == 0x8877665544332211);
    CHECK(parsed.f_bu64()[2] == 0xffeeddccbbaa0099);
    tako::require_same<decltype(parsed.f_bu64()[0]), uint64_t>();

    Arrays owned {
        .f_i8 = {0x01, 0x02, 0x03},
        .f_li16 = {
            static_cast<int16_t>(0x4321),
            static_cast<int16_t>(0x8765),
            static_cast<int16_t>(0xba09),
        },
        .f_li32 = {
            static_cast<int32_t>(0x87654321),
            static_cast<int32_t>(0xfedcba09),
            static_cast<int32_t>(0x44332211),
        },
        .f_li64 = {
            static_cast<int64_t>(0xfedcba0987654321),
            static_cast<int64_t>(0x8877665544332211),
            static_cast<int64_t>(0xffeeddccbbaa0099),
        },
        .f_bi16 = {
            static_cast<int16_t>(0x4321),
            static_cast<int16_t>(0x8765),
            static_cast<int16_t>(0xba09),
        },
        .f_bi32 = {
            static_cast<int32_t>(0x87654321),
            static_cast<int32_t>(0xfedcba09),
            static_cast<int32_t>(0x44332211),
        },
        .f_bi64 = {
            static_cast<int64_t>(0xfedcba0987654321),
            static_cast<int64_t>(0x8877665544332211),
            static_cast<int64_t>(0xffeeddccbbaa0099),
        },
        .f_u8 = {0x01, 0x02, 0x03},
        .f_lu16 = {0x4321, 0x8765, 0xba09},
        .f_lu32 = {0x87654321, 0xfedcba09, 0x44332211},
        .f_lu64 = {0xfedcba0987654321, 0x8877665544332211, 0xffeeddccbbaa0099},
        .f_bu16 = {0x4321, 0x8765, 0xba09},
        .f_bu32 = {0x87654321, 0xfedcba09, 0x44332211},
        .f_bu64 = {0xfedcba0987654321, 0x8877665544332211, 0xffeeddccbbaa0099},
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("enums") {
    auto data = tako::byte_array(
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
    auto parsed = tako::expect_parse<EnumsView>(data);

    CHECK(parsed.u8_enum() == U8Enum::THING_3);
    CHECK(parsed.bu64_enum() == BU64Enum::THING_1);
    CHECK(parsed.u8_enum_array()[0] == U8Enum::THING_0);
    CHECK(parsed.u8_enum_array()[1] == U8Enum::THING_1);
    CHECK(parsed.u8_enum_array()[2] == U8Enum::THING_3);
    CHECK(parsed.bu64_enum_array()[0] == BU64Enum::THING_0);
    CHECK(parsed.bu64_enum_array()[1] == BU64Enum::THING_1);
    CHECK(parsed.bu64_enum_array()[2] == BU64Enum::THING_2);

    Enums owned {
        .u8_enum = U8Enum::THING_3,
        .bu64_enum = BU64Enum::THING_1,
        .u8_enum_array = {U8Enum::THING_0, U8Enum::THING_1, U8Enum::THING_3},
        .bu64_enum_array = {BU64Enum::THING_0, BU64Enum::THING_1, BU64Enum::THING_2},
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("cookie_order_pair") {
    auto data = tako::byte_array(
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
    auto parsed = tako::expect_parse<CookieOrderPairView>(data);

    CHECK(parsed.order_1().quantity() == 10);
    CHECK(parsed.order_1().flavor() == Flavor::VANILLA);
    CHECK(parsed.order_2().quantity() == 11);
    CHECK(parsed.order_2().flavor() == Flavor::CHOCOLATE);

    CookieOrderPair owned {
        .order_1 = CookieOrder {
            .quantity = 10,
            .flavor = Flavor::VANILLA,
        },
        .order_2 = CookieOrder {
            .quantity = 11,
            .flavor = Flavor::CHOCOLATE,
        },
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("cookie_order_list") {
    auto data = tako::byte_array(
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
    auto parsed = tako::expect_parse<CookieOrderListView>(data);

    CHECK(parsed.number_of_orders() == 3);
    CHECK(parsed.orders()[0].quantity() == 10);
    CHECK(parsed.orders()[0].flavor() == Flavor::VANILLA);
    CHECK(parsed.orders()[1].quantity() == 11);
    CHECK(parsed.orders()[1].flavor() == Flavor::CHOCOLATE);
    CHECK(parsed.orders()[2].quantity() == 12);
    CHECK(parsed.orders()[2].flavor() == Flavor::CHOCOLATE);

    CookieOrderList owned {
        .orders = {
            CookieOrder {
                .quantity = 10,
                .flavor = Flavor::VANILLA,
            },
            CookieOrder {
                .quantity = 11,
                .flavor = Flavor::CHOCOLATE,
            },
            CookieOrder {
                .quantity = 12,
                .flavor = Flavor::CHOCOLATE,
            },
        },
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("vector") {
    auto data = tako::byte_array(
        // len (bi32)
        0x00, 0x00, 0x00, 0x03,
        // data (Seq(bi32, this.len))
        0xde, 0xad, 0xbe, 0xef,
        0xca, 0xfe, 0xba, 0xbe,
        0x00, 0xc0, 0xff, 0xee
    );
    auto parsed = tako::expect_parse<VectorView>(data);

    CHECK(parsed.len() == 3);
    CHECK(parsed.data()[0] == 0xdeadbeef);
    CHECK(parsed.data()[1] == 0xcafebabe);
    CHECK(parsed.data()[2] == 0x00c0ffee);

    Vector owned {
        .data = {
            static_cast<int32_t>(0xdeadbeef),
            static_cast<int32_t>(0xcafebabe),
            static_cast<int32_t>(0x00c0ffee),
        },
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("vector_pair") {
    auto data = tako::byte_array(
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
    auto parsed = tako::expect_parse<VectorPairView>(data);

    CHECK(parsed.v1().len() == 3);
    CHECK(parsed.v1().data()[0] == 0xdeadbeef);
    CHECK(parsed.v1().data()[1] == 0xcafebabe);
    CHECK(parsed.v1().data()[2] == 0x00c0ffee);
    CHECK(parsed.v2().len() == 1);
    CHECK(parsed.v2().data()[0] == 0x11111111);

    VectorPair owned {
        .v1 = Vector {
            .data = {
                static_cast<int32_t>(0xdeadbeef),
                static_cast<int32_t>(0xcafebabe),
                static_cast<int32_t>(0x00c0ffee),
            },
        },
        .v2 = Vector {
            .data = {
                static_cast<int32_t>(0x11111111),
            },
        },
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("matrix") {
    auto data = tako::byte_array(
        // data = [[0x1, 0x2, 0x3], [0x4, 0x5, 0x6], [0x7, 0x8, 0x9]] ([[i8; 3]; 3])
        0x1, 0x2, 0x3,
        0x4, 0x5, 0x6,
        0x7, 0x8, 0x9
    );
    auto parsed = tako::expect_parse<MatrixView>(data);

    CHECK(parsed.data()[0][0] == 0x1);
    CHECK(parsed.data()[0][1] == 0x2);
    CHECK(parsed.data()[0][2] == 0x3);
    CHECK(parsed.data()[1][0] == 0x4);
    CHECK(parsed.data()[1][1] == 0x5);
    CHECK(parsed.data()[1][2] == 0x6);
    CHECK(parsed.data()[2][0] == 0x7);
    CHECK(parsed.data()[2][1] == 0x8);
    CHECK(parsed.data()[2][2] == 0x9);

    Matrix owned {
        .data = {
            std::array<std::int8_t, 3>{0x1, 0x2, 0x3},
            std::array<std::int8_t, 3>{0x4, 0x5, 0x6},
            std::array<std::int8_t, 3>{0x7, 0x8, 0x9},
        },
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("var_matrix") {
    // Parse the virtual field data
    auto data = tako::byte_array(
        // rows = 4 (u8)
        0x4,
        // data = [[0x1, 0x2, 0x3], [0x4, 0x5, 0x6], [0x7, 0x8, 0x9], [0xa, 0xb, 0xc]] ([[i8; 3]; rows])
        0x1, 0x2, 0x3,
        0x4, 0x5, 0x6,
        0x7, 0x8, 0x9,
        0xa, 0xb, 0xc
    );
    auto parse_result = tako::expect_parse_full<VarListView>(data);
    auto parsed = parse_result.rendered;

    CHECK(parsed.rows() == 0x4);

    auto try_data = parsed.data(parse_result.tail);
    REQUIRE(bool(try_data));
    auto p_data = try_data->rendered;
    CHECK(p_data[0][0] == 0x1);
    CHECK(p_data[0][1] == 0x2);
    CHECK(p_data[0][2] == 0x3);
    CHECK(p_data[1][0] == 0x4);
    CHECK(p_data[1][1] == 0x5);
    CHECK(p_data[1][2] == 0x6);
    CHECK(p_data[2][0] == 0x7);
    CHECK(p_data[2][1] == 0x8);
    CHECK(p_data[2][2] == 0x9);
    CHECK(p_data[3][0] == 0xa);
    CHECK(p_data[3][1] == 0xb);
    CHECK(p_data[3][2] == 0xc);
}

TEST_CASE("person") {
    auto data = tako::byte_array(
        // name (External.String)
        // len (li32)
        0x03, 0x00, 0x00, 0x00,
        // data (Seq(i8, this.len))
        98, 111, 98,
        // age (li16)
        0x04, 0x00
    );
    auto parsed = tako::expect_parse<PersonView>(data);

    CHECK(parsed.name().len() == 3);
    CHECK(parsed.name().data()[0] == 'b');
    CHECK(parsed.name().data()[1] == 'o');
    CHECK(parsed.name().data()[2] == 'b');
    CHECK(parsed.age() == 4);

    Person owned {
        .name = String {
            .data = tako::make_string("bob"),
        },
        .age = 4,
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("box") {
    auto data = tako::byte_array(
        // length (li16)
        0x01, 0x00,
        // width (li16)
        0x02, 0x00,
        // height (li16)
        0x03, 0x00
    );
    auto parsed = tako::expect_parse<BoxView>(data);

    CHECK(parsed.length() == 1);
    CHECK(parsed.width() == 2);
    CHECK(parsed.height() == 3);

    Box owned {
        .length = 1,
        .width = 2,
        .height = 3,
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("pencil") {
    auto data = tako::byte_array(
        // lead_number (i8)
        0x02,
        // color (External.Color(lu32))
        0x06, 0x00, 0x00, 0x00
    );
    auto parsed = tako::expect_parse<PencilView>(data);

    CHECK(parsed.lead_number() == 2);
    CHECK(parsed.color() == Color::VIOLET);

    Pencil owned {
        .lead_number = 2,
        .color = Color::VIOLET,
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("thing_person") {
    auto data = tako::byte_array(
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
    auto parsed = tako::expect_parse<ThingMsgView>(data);

    auto person = tako::expect_type<PersonView>(parsed.thing());
    CHECK(person.name().len() == 3);
    CHECK(person.name().data()[0] == 'b');
    CHECK(person.name().data()[1] == 'o');
    CHECK(person.name().data()[2] == 'b');
    CHECK(person.age() == 4);

    ThingMsg owned {
        .thing = Person {
            .name = String {
                .data = tako::make_string("bob"),
            },
            .age = 4,
        },
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("thing_box") {
    auto data = tako::byte_array(
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
    auto parsed = tako::expect_parse<ThingMsgView>(data);

    auto box = tako::expect_type<BoxView>(parsed.thing());
    CHECK(box.length() == 1);
    CHECK(box.width() == 2);
    CHECK(box.height() == 3);

    ThingMsg owned {
        .thing = Box {
            .length = 1,
            .width = 2,
            .height = 3,
        },
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("thing_pencil") {
    auto data = tako::byte_array(
        // thing_type (Thing.tag_type(u8))
        0x02,
        // thing
        // lead_number (i8)
        0x02,
        // color (External.Color(lu32))
        0x06, 0x00, 0x00, 0x00
    );
    auto parsed = tako::expect_parse<ThingMsgView>(data);

    auto pencil = tako::expect_type<PencilView>(parsed.thing());
    CHECK(pencil.lead_number() == 2);
    CHECK(pencil.color() == Color::VIOLET);


    ThingMsg owned {
        .thing = Pencil {
            .lead_number = 2,
            .color = Color::VIOLET,
        },
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("two_thing_pencil") {
    auto data = tako::byte_array(
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
    auto parsed = tako::expect_parse<TwoThingMsgView>(data);

    auto pencil1 = tako::expect_type<PencilView>(parsed.thing1());
    CHECK(pencil1.lead_number() == 2);
    CHECK(pencil1.color() == Color::VIOLET);
    auto pencil2 = tako::expect_type<PencilView>(parsed.thing2());
    CHECK(pencil2.lead_number() == 1);
    CHECK(pencil2.color() == Color::VIOLET);


    TwoThingMsg owned {
        .thing1 = Pencil {
            .lead_number = 2,
            .color = Color::VIOLET,
        },
        .thing2 = Pencil {
            .lead_number = 1,
            .color = Color::VIOLET,
        },
    };
    CHECK(tako::consistent(data, owned, parsed));
}

TEST_CASE("thing_virtual_pencil") {
    auto data = tako::byte_array(
        // thing_type (Thing.tag_type(u8))
        0x02,
        // thing
        // lead_number (i8)
        0x02,
        // color (External.Color(lu32))
        0x06, 0x00, 0x00, 0x00
    );
    tako::ParseInfo<VirtualThingMsgView> result = tako::expect_parse_full<VirtualThingMsgView>(data);
    VirtualThingMsgView parsed = result.rendered;

    tako::ParseResult<ThingView> try_thing = parsed.thing(result.tail);
    REQUIRE(bool(try_thing));
    ThingView thing = try_thing->rendered;

    auto pencil = tako::expect_type<PencilView>(thing);
    CHECK(pencil.lead_number() == 2);
    CHECK(pencil.color() == Color::VIOLET);

    VirtualThingMsg owned {
        .thing_type = 2,
    };
    Pencil owned_thing {
        .lead_number = 2,
        .color = Color::VIOLET,
    };
    std::vector<gsl::byte> built{owned.size_bytes() + owned_thing.size_bytes()};
    gsl::span<gsl::byte> tail = owned.serialize_into(built);
    owned_thing.serialize_into(tail);
    CHECK(tako::buf_equals(data, built));
}
