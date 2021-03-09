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

#include <type_traits>

#include "tako/ptypes_runtime.hh"
#include "tako/helpers.hh"

#include "catch2/catch.hpp"
#include "tako/ptypes.hh"
#include "test_types/ptypes_test_types.hh"

using namespace test_types;
using namespace tako;

template <typename T>
static void simple_string_test() {
    std::string_view input = "hello world";
    auto str = make_ptype_string<T>(input).value();
    CHECK(make_string_view(str) == input);
}
TEST_CASE("ptype_string") {
    simple_string_test<ptypes::StringL8>();
    simple_string_test<ptypes::StringL16>();
    simple_string_test<ptypes::StringL32>();
}

TEST_CASE("ptype_maybe_num") {
    ptypes_test_types::Optional some_num {.maybe_num = ptypes::Lu32 {.value = 42}};
    ptypes_test_types::Optional none_num = {.maybe_num = ptypes::Empty {}};

    some_num.maybe_num.match(
        [&](const ptypes::Empty&) { CHECK(false); },
        [&](const ptypes::Lu32& some) { CHECK(some.value == 42); }
    );

   none_num.maybe_num.match(
        [&](const ptypes::Empty&) { },
        [&](const ptypes::Lu32&) { CHECK(false); }
    );

    auto some_num_data = some_num.serialize();
    auto some_num_parsed = expect_parse<ptypes_test_types::OptionalView>(some_num_data);

    auto none_num_data = none_num.serialize();
    auto none_num_parsed = expect_parse<ptypes_test_types::OptionalView>(none_num_data);

    some_num_parsed.maybe_num().match(
        [&](const ptypes::EmptyView&) { CHECK(false); },
        [&](const ptypes::Lu32View& some) { CHECK(some.value() == 42); }
    );

    none_num_parsed.maybe_num().match(
        [&](const ptypes::EmptyView&) { },
        [&](const ptypes::Lu32View&) { CHECK(false); }
    );
}
