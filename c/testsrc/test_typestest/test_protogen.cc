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
#include "catch2/catch.hpp"
#include "test_types/protogen/basic.hh"
#include "test_types/protogen/basic_pair.hh"
#include "test_types/protogen/basic_transform.hh"

using namespace test_types::protogen;

TEST_CASE("protogen_basic") {
    STATIC_REQUIRE(std::is_class<basic::Foo>::value);
    STATIC_REQUIRE(std::is_class<basic::Bar>::value);
}

TEST_CASE("protogen_basic_pair") {
    STATIC_REQUIRE(std::is_class<basic_pair::FooPair>::value);
}

TEST_CASE("protogen_basic_transform") {
    STATIC_REQUIRE(std::is_class<basic_transform::Foo>::value);
    STATIC_REQUIRE(std::is_class<basic_transform::Bar>::value);
    STATIC_REQUIRE(std::is_class<basic_transform::Msg>::value);
}
