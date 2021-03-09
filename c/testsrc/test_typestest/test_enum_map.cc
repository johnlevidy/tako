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
#include "tako/enum_map.hh"
#include "test_types/enum_name.hh"

using namespace test_types::enum_name;

TEST_CASE("enum_map_empty") {
    tako::EnumMap<Dolphins, int32_t> map;
    CHECK(map.empty());
}

TEST_CASE("enum_map_insert") {
    tako::EnumMap<Dolphins, int32_t> map;
    map[Dolphins::COMMON] = 2;
    map[Dolphins::PACIFIC_WHITE_SIDED] = 42;
    CHECK(map[Dolphins::COMMON] == 2);
    CHECK(map[Dolphins::PACIFIC_WHITE_SIDED] == 42);
}

