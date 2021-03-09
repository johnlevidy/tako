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
#include "test_types/conversions.hh"
#include <type_traits>

using namespace test_types::conversions;
using namespace std;

TEST_CASE("conversions_flavor_old_to_flavor_new") {
    auto old = FlavorOld::CHOCOLATE;
    auto new_ = convert(old, tako::Type<FlavorNew>{});
    CHECK(new_ == FlavorNew::CHOCOLATE);
}

TEST_CASE("conversions_flavor_new_to_flavor_old") {
    auto new_ = FlavorNew::CARMEL;
    auto old = convert(new_, tako::Type<FlavorOld>{});
    CHECK(old == FlavorOld::CHOCOLATE);
}

TEST_CASE("conversions_cupcake_order_old_to_cupcacke_order_new") {
    auto old = CupcakeOrderOld {.flavor = FlavorOld::CHOCOLATE};
    auto new_ = convert(old, tako::Type<CupcakeOrderNew>{});
    CHECK(new_ == CupcakeOrderNew{.flavor = FlavorNew::CHOCOLATE, .quantity = 50});
}

TEST_CASE("conversions_cupcake_order_new_to_cupcacke_order_old") {
    auto new_ = CupcakeOrderNew{.flavor = FlavorNew::CARMEL, .quantity = 50};
    auto old = convert(new_, tako::Type<CupcakeOrderOld>{});
    CHECK(old == CupcakeOrderOld {.flavor = FlavorOld::CHOCOLATE});
}
TEST_CASE("conversions_order_old_to_order_new") {
    auto old = OrderOld{CupcakeOrderOld {.flavor = FlavorOld::CHOCOLATE}};
    auto new_ = convert(old, tako::Type<OrderNew>{});
    // Catch tries to stringify stuff because the variant has operator << but
    // the underlying types don't so it fails
    CHECK(new_ == OrderNew {CupcakeOrderNew{.flavor = FlavorNew::CHOCOLATE, .quantity = 50}});
}
TEST_CASE("conversions_order_new_to_order_old") {
    auto new_ = OrderNew{CupcakeOrderNew{.flavor = FlavorNew::CARMEL, .quantity = 50}};
    auto old = convert(new_, tako::Type<OrderOld>{});
    CHECK(old == OrderOld {CupcakeOrderOld {.flavor = FlavorOld::CHOCOLATE}});
}

TEST_CASE("conversions_msg_old_to_msg_new") {
    auto old = MsgOld{OrderOld{CupcakeOrderOld {.flavor = FlavorOld::CHOCOLATE}}};
    // I think something is weird about boost::variant, clang-tidy comlains: https://github.com/boostorg/variant/issues/48
    // TODO: switch to std::variant once we have C++17.
    auto new_ = convert(old, tako::Type<MsgNew>{}); // NOLINT
    CHECK(new_ == MsgNew {OrderNew {CupcakeOrderNew{.flavor = FlavorNew::CHOCOLATE, .quantity = 50}}}); // NOLINT
}

TEST_CASE("conversions_msg_new_to_msg_old") {
    auto new_ = MsgNew{OrderNew{CupcakeOrderNew{.flavor = FlavorNew::CARMEL, .quantity = 50}}};
    auto old = convert(new_, tako::Type<MsgOld>{});
    CHECK(old == MsgOld {OrderOld {CupcakeOrderOld {.flavor = FlavorOld::CHOCOLATE}}});
}

TEST_CASE("conversions_view_cake_order_old_to_cake_order_new") {
    auto old_bytes = CakeOrderOld {.flavor = FlavorOld::CHOCOLATE}.serialize();
    auto old_view = tako::expect_parse<CakeOrderOldView>(old_bytes);
    // Transparent conversion taking some bytes and interpreting them as the newer
    // message
    auto new_view = convert(old_view, tako::Type<CakeOrderNewView>{});
    CHECK(new_view.build() == CakeOrderNew{.flavor = FlavorNew::CHOCOLATE});
}
