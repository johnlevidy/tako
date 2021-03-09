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
#include "test_types/enum_range.hh"
#include <type_traits>

using namespace test_types::basic;
using namespace test_types::enum_range;

TEST_CASE("parse_errors_thing_msg") {
    auto variant_to_short = tako::byte_array(
        // thing_type (Thing.tag_type(u8))
        0x00
        // thing
        // NOTE IT IS NOT ACTUALLY THERE
    );
    auto string_to_short = tako::byte_array(
        // thing_type (Thing.tag_type(u8))
        0x00,
        // thing
        // name (External.String)
        // len (li32)
        0x03, 0x00, 0x00, 0x00,
        // data (Seq(i8, this.len))
        // NOTE THERE IS NOT ENOUGH DATA
        // Only 2 chars
        98, 111
    );
    auto malformed = tako::byte_array(
        // thing_type (Thing.tag_type(u8))
        // NOTE NOT A VALID THING TYPE
        0xFF
    );

    CHECK(tako::expect_parse_fail<ThingMsgView>(variant_to_short) == tako::ParseError::NOT_ENOUGH_DATA);
    CHECK(tako::expect_parse_fail<ThingMsgView>(string_to_short) == tako::ParseError::NOT_ENOUGH_DATA);
    CHECK(tako::expect_parse_fail<ThingMsgView>(malformed) == tako::ParseError::MALFORMED);
}

TEST_CASE("parse_errors_enum") {
    auto thing_ff = tako::byte_array(0xff);
    auto thing_00 = tako::byte_array(0x00);
    auto thing_01 = tako::byte_array(0x01);
    auto thing_02 = tako::byte_array(0x02);
    auto thing_03 = tako::byte_array(0x03);

    CHECK(tako::expect_parse_fail<Enum02MsgView>(thing_ff) == tako::ParseError::MALFORMED);
    tako::expect_parse_to<Enum02MsgView>(thing_00, Enum02Msg {.thing = Enum02::THING0});
    tako::expect_parse_to<Enum02MsgView>(thing_01, Enum02Msg {.thing = Enum02::THING1});
    tako::expect_parse_to<Enum02MsgView>(thing_02, Enum02Msg {.thing = Enum02::THING2});
    CHECK(tako::expect_parse_fail<Enum02MsgView>(thing_03) == tako::ParseError::MALFORMED);

    auto unsafe_ff = Enum02MsgView::render(thing_ff);
    CHECK(unsafe_ff.thing() == Enum02::make_unsafe(0xff));
    auto unsafe_03 = Enum02MsgView::render(thing_03);
    CHECK(unsafe_03.thing() == Enum02::make_unsafe(0x03));
}
