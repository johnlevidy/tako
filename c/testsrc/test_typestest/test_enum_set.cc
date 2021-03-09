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
#include <iterator>
#include <vector>
#include "catch2/catch.hpp"
#include "tako/helpers.hh"
#include "tako/enum_set.hh"
#include "test_types/enum_name.hh"
#include "test_types/offset_enum.hh"

using namespace test_types::enum_name;
using namespace test_types::offset_enum;

TEST_CASE("enum_set_ctor_empty") {
    tako::EnumSet<Dolphins> set;
    CHECK(set.empty());
}

TEST_CASE("enum_set_ctor_iter") {
    auto arr = {Dolphins::COMMON, Dolphins::PACIFIC_WHITE_SIDED};
    tako::EnumSet<Dolphins> set(arr.begin(), arr.end());
    CHECK(set.size() == 2);
    CHECK(set.contains(Dolphins::COMMON));
    CHECK(set.contains(Dolphins::PACIFIC_WHITE_SIDED));
    CHECK_FALSE(set.contains(Dolphins::BOTTLENOSE));
    CHECK_FALSE(set.contains(Dolphins::SPINNER));
    CHECK_FALSE(set.contains(Dolphins::PILOT_WHALE));
}

TEST_CASE("enum_set_ctor_initialilzer_list") {
    tako::EnumSet<Dolphins> set{Dolphins::COMMON, Dolphins::PACIFIC_WHITE_SIDED};
    CHECK(set.size() == 2);
    CHECK(set.contains(Dolphins::COMMON));
    CHECK(set.contains(Dolphins::PACIFIC_WHITE_SIDED));
    CHECK_FALSE(set.contains(Dolphins::BOTTLENOSE));
    CHECK_FALSE(set.contains(Dolphins::SPINNER));
    CHECK_FALSE(set.contains(Dolphins::PILOT_WHALE));
}

template <typename T>
static void test_iter(std::initializer_list<T> stuff) {
    tako::EnumSet<T> set{stuff};
    SECTION("non-const") {
        std::vector<T> vec;
        std::copy(set.begin(), set.end(), std::back_inserter(vec));
        CHECK(vec == std::vector<T>{stuff});
    }
    SECTION("const") {
        std::vector<T> vec;
        std::copy(set.cbegin(), set.cend(), std::back_inserter(vec));
        CHECK(vec == std::vector<T>{stuff});
    }
}

TEST_CASE("enum_set_iter") {
    test_iter({Dolphins::COMMON, Dolphins::PACIFIC_WHITE_SIDED});
    test_iter({Dolphins::PACIFIC_WHITE_SIDED});
    test_iter({Dolphins::PILOT_WHALE});
    test_iter({Dolphins::COMMON, Dolphins::BOTTLENOSE, Dolphins::SPINNER, Dolphins::PACIFIC_WHITE_SIDED, Dolphins::PILOT_WHALE});
}

TEST_CASE("enum_set_iter_pointer") {
    auto set = tako::make_enum_set(Dolphins::COMMON);
    CHECK(set.begin()->value() == Dolphins::COMMON.value());
}

TEST_CASE("enum_set_empty") {
    CHECK(tako::make_enum_set<Dolphins>().empty());
    CHECK_FALSE(tako::make_enum_set(Dolphins::COMMON).empty());
}

TEST_CASE("enum_set_size") {
    CHECK(tako::make_enum_set<Dolphins>().size() == 0);
    CHECK(tako::make_enum_set(Dolphins::COMMON).size() == 1);
    CHECK(tako::make_enum_set(Dolphins::COMMON, Dolphins::BOTTLENOSE).size() == 2);
}

TEST_CASE("enum_set_max_size") {
    CHECK(tako::make_enum_set<Dolphins>().max_size() == 5);
}

TEST_CASE("enum_set_clear") {
    auto set = tako::make_enum_set(Dolphins::COMMON);
    CHECK_FALSE(set.empty());
    set.clear();
    CHECK(set.empty());
}

TEST_CASE("enum_set_insert") {
    auto set = tako::make_enum_set<Dolphins>();
    CHECK_FALSE(set.contains(Dolphins::SPINNER));
    set.insert(Dolphins::SPINNER);
    CHECK(set.contains(Dolphins::SPINNER));
}

TEST_CASE("enum_set_insert_iter") {
    auto set1 = tako::make_enum_set(Dolphins::SPINNER, Dolphins::PILOT_WHALE);
    auto set2 = tako::make_enum_set<Dolphins>();
    set2.insert(set1.begin(), set1.end());
    CHECK(set1 == set2);
}

TEST_CASE("enum_set_erase") {
    auto set = tako::make_enum_set(Dolphins::COMMON, Dolphins::SPINNER, Dolphins::PACIFIC_WHITE_SIDED, Dolphins::PILOT_WHALE);
    set.erase(Dolphins::SPINNER);
    set.erase(Dolphins::PACIFIC_WHITE_SIDED);
    CHECK(set.contains(Dolphins::COMMON));
    CHECK(set.contains(Dolphins::PILOT_WHALE));
    CHECK(set.size() == 2);
}

TEST_CASE("enum_set_erase_iter") {
    auto set = tako::make_enum_set(Dolphins::COMMON, Dolphins::SPINNER, Dolphins::PACIFIC_WHITE_SIDED, Dolphins::PILOT_WHALE);
    set.erase(set.find(Dolphins::SPINNER), set.find(Dolphins::PILOT_WHALE));
    CHECK(set.contains(Dolphins::COMMON));
    CHECK(set.contains(Dolphins::PILOT_WHALE));
    CHECK(set.size() == 2);
}

TEST_CASE("enum_set_count") {
    auto set = tako::make_enum_set(Dolphins::COMMON);
    CHECK(set.count(Dolphins::COMMON) == 1);
    CHECK(set.count(Dolphins::PACIFIC_WHITE_SIDED) == 0);
}

TEST_CASE("enum_set_find") {
    auto set = tako::make_enum_set(Dolphins::COMMON);
    REQUIRE(set.find(Dolphins::COMMON) != set.end());
    CHECK(*set.find(Dolphins::COMMON) == Dolphins::COMMON);
    CHECK(set.find(Dolphins::PACIFIC_WHITE_SIDED) == set.end());
}

TEST_CASE("enum_set_equal_range") {
    auto set = tako::make_enum_set(Dolphins::COMMON, Dolphins::SPINNER);
    SECTION("good") {
        auto [begin, end] = set.equal_range(Dolphins::COMMON);
        CHECK(begin == set.begin());
        CHECK(end == set.find(Dolphins::SPINNER));
    }
    SECTION("bad") {
        auto [begin, end] = set.equal_range(Dolphins::PACIFIC_WHITE_SIDED);
        CHECK(begin == set.end());
        CHECK(end == set.end());
    }
}

TEST_CASE("enum_set_equals") {
    auto set1 = tako::make_enum_set(Dolphins::COMMON, Dolphins::SPINNER);
    auto set2 = tako::make_enum_set(Dolphins::COMMON);
    CHECK(set1 == set1);
    CHECK(set2 != set1);
}

TEST_CASE("enum_set_offset") {
    SECTION("all") {
        auto set = tako::make_enum_set(Offset::LOW, Offset::MID, Offset::HIGH);
        REQUIRE(set.find(Offset::LOW) != set.end());
        CHECK(*set.find(Offset::LOW) == Offset::LOW);
        REQUIRE(set.find(Offset::MID) != set.end());
        CHECK(*set.find(Offset::MID) == Offset::MID);
        REQUIRE(set.find(Offset::HIGH) != set.end());
        CHECK(*set.find(Offset::HIGH) == Offset::HIGH);
    }
    SECTION("some") {
        auto set = tako::make_enum_set(Offset::LOW, Offset::HIGH);
        REQUIRE(set.find(Offset::LOW) != set.end());
        CHECK(*set.find(Offset::LOW) == Offset::LOW);
        CHECK(set.find(Offset::MID) == set.end());
        REQUIRE(set.find(Offset::HIGH) != set.end());
        CHECK(*set.find(Offset::HIGH) == Offset::HIGH);
    }
}

TEST_CASE("enum_set_constexpr") {
    constexpr auto set = tako::make_enum_set(Dolphins::COMMON, Dolphins::SPINNER);
    STATIC_REQUIRE(set.contains(Dolphins::COMMON));
    STATIC_REQUIRE(set.contains(Dolphins::SPINNER));
    STATIC_REQUIRE_FALSE(set.contains(Dolphins::BOTTLENOSE));
    STATIC_REQUIRE_FALSE(set.contains(Dolphins::PACIFIC_WHITE_SIDED));
    STATIC_REQUIRE_FALSE(set.contains(Dolphins::PILOT_WHALE));
}

TEST_CASE("enum_set_ullong") {
    auto set = tako::make_enum_set(Dolphins::COMMON, Dolphins::SPINNER);
    CHECK(set.to_ullong() == 0x0000000000000005);
    CHECK(tako::EnumSet<Dolphins>(set.to_ullong()) == set);
}

TEST_CASE("enum_set_offset_ullong") {
    auto set = tako::make_enum_set(SimpleOffset::LOW, SimpleOffset::HIGH);
    CHECK(set.to_ullong() == 0x0000000000050000);
    CHECK(tako::EnumSet<SimpleOffset>(set.to_ullong()) == set);
}

TEST_CASE("enum_set_ullong_full_range_constexpr") {
    constexpr auto set = tako::make_enum_set(Range64::LOW, Range64::HIGH);
    CHECK(set.to_ullong() == 0x8000000000000001);
    CHECK(tako::EnumSet<Range64>(set.to_ullong()) == set);
}
