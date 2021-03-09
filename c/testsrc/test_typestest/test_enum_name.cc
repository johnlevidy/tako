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

#include <algorithm>
#include "catch2/catch.hpp"
#include "tako/helpers.hh"
#include "test_types/enum_name.hh"

using namespace test_types::enum_name;

TEST_CASE("enum_name") {
    CHECK(Dolphins::COMMON.name() == "COMMON");
    CHECK(Dolphins::BOTTLENOSE.name() == "BOTTLENOSE");
    CHECK(Dolphins::SPINNER.name() == "SPINNER");
    CHECK(Dolphins::PACIFIC_WHITE_SIDED.name() == "PACIFIC_WHITE_SIDED");
    CHECK(Dolphins::PILOT_WHALE.name() == "PILOT_WHALE");
}

template <typename C, typename T>
static bool contains(const C& c, const T& t) {
    return std::find(c.begin(), c.end(), t) != c.end();
}

TEST_CASE("enum_properties") {
    STATIC_REQUIRE(Dolphins::VALUES.size() == 5);
    CHECK(contains(Dolphins::VALUES, Dolphins::COMMON));
    CHECK(contains(Dolphins::VALUES, Dolphins::BOTTLENOSE));
    CHECK(contains(Dolphins::VALUES, Dolphins::SPINNER));
    CHECK(contains(Dolphins::VALUES, Dolphins::PACIFIC_WHITE_SIDED));
    CHECK(contains(Dolphins::VALUES, Dolphins::PILOT_WHALE));
}

