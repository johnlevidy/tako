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
#include "test_types/external.hh"

#include <iostream>
#include <type_traits>

using namespace test_types::basic;
using namespace test_types::external;

template <typename T>
void test_json_roundtrip(const T& x) {
    auto as_json = serialize_json(x);
    INFO(as_json.dump(4));
    CHECK(parse_json(as_json, tako::Type<T>{}) == x);
}

TEST_CASE("json_primitives") {
    test_json_roundtrip<Primitives>({
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
    });
}

TEST_CASE("json_arrays") {
    test_json_roundtrip<Arrays>({
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
    });
}

TEST_CASE("json_enums") {
    test_json_roundtrip<Enums>({
        .u8_enum = U8Enum::THING_3,
        .bu64_enum = BU64Enum::THING_1,
        .u8_enum_array = {U8Enum::THING_0, U8Enum::THING_1, U8Enum::THING_3},
        .bu64_enum_array = {BU64Enum::THING_0, BU64Enum::THING_1, BU64Enum::THING_2},
    });
}

TEST_CASE("json_cookie_order_pair") {
    test_json_roundtrip<CookieOrderPair>({
        .order_1 = CookieOrder {
            .quantity = 10,
            .flavor = Flavor::VANILLA,
        },
        .order_2 = CookieOrder {
            .quantity = 11,
            .flavor = Flavor::CHOCOLATE,
        },
    });
}

TEST_CASE("json_cookie_order_list") {
    test_json_roundtrip<CookieOrderList>({
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
    });
}

TEST_CASE("json_vector") {
    test_json_roundtrip<Vector>({
        .data = {
            static_cast<int32_t>(0xdeadbeef),
            static_cast<int32_t>(0xcafebabe),
            static_cast<int32_t>(0x00c0ffee),
        },
    });
}

TEST_CASE("json_matrix") {
    test_json_roundtrip<Matrix>({
        .data = {
            std::array<std::int8_t, 3>{0x1, 0x2, 0x3},
            std::array<std::int8_t, 3>{0x4, 0x5, 0x6},
            std::array<std::int8_t, 3>{0x7, 0x8, 0x9},
        },
    });
}

TEST_CASE("json_person") {
    test_json_roundtrip<Person>({
        .name = String {
            .data = tako::make_string("bob"),
        },
        .age = 4,
    });
}

TEST_CASE("json_box") {
    test_json_roundtrip<Box>({
        .length = 1,
        .width = 2,
        .height = 3,
    });
}

TEST_CASE("json_pencil") {
    test_json_roundtrip<Pencil>({
        .lead_number = 2,
        .color = Color::VIOLET,
    });
}

TEST_CASE("json_thing_person") {
    test_json_roundtrip<ThingMsg>({
        .thing = Person {
            .name = String {
                .data = tako::make_string("bob"),
            },
            .age = 4,
        },
    });
}

TEST_CASE("json_thing_box") {
    test_json_roundtrip<ThingMsg>({
        .thing = Box {
            .length = 1,
            .width = 2,
            .height = 3,
        },
    });
}

TEST_CASE("json_thing_pencil") {
    test_json_roundtrip<ThingMsg>({
        .thing = Pencil {
            .lead_number = 2,
            .color = Color::VIOLET,
        },
    });
}

TEST_CASE("json_two_thing_pencil") {
    test_json_roundtrip<TwoThingMsg>({
        .thing1 = Pencil {
            .lead_number = 2,
            .color = Color::VIOLET,
        },
        .thing2 = Pencil {
            .lead_number = 1,
            .color = Color::VIOLET,
        },
    });
}
