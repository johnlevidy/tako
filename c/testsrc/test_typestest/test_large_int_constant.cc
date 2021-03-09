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
#include "test_types/large_int_constant.hh"

using namespace test_types::large_int_constant;

template <typename T, typename U>
static void check(T a, U b) {
    tako::require_same<T, U>();
    CHECK(a == b);
}

TEST_CASE("large_int_constant") {
    check(C_I8_MIN, static_cast<::std::int8_t>(-UINT8_C(128)));
    check(C_I8_MAX, static_cast<::std::int8_t>(UINT8_C(127)));
    check(C_LI16_MIN, static_cast<::std::int16_t>(-UINT16_C(32768)));
    check(C_LI16_MAX, static_cast<::std::int16_t>(UINT16_C(32767)));
    check(C_LI32_MIN, static_cast<::std::int32_t>(-UINT32_C(2147483648)));
    check(C_LI32_MAX, static_cast<::std::int32_t>(UINT32_C(2147483647)));
    check(C_LI64_MIN, static_cast<::std::int64_t>(-UINT64_C(9223372036854775808)));
    check(C_LI64_MAX, static_cast<::std::int64_t>(UINT64_C(9223372036854775807)));
    check(C_BI16_MIN, static_cast<::std::int16_t>(-UINT16_C(32768)));
    check(C_BI16_MAX, static_cast<::std::int16_t>(UINT16_C(32767)));
    check(C_BI32_MIN, static_cast<::std::int32_t>(-UINT32_C(2147483648)));
    check(C_BI32_MAX, static_cast<::std::int32_t>(UINT32_C(2147483647)));
    check(C_BI64_MIN, static_cast<::std::int64_t>(-UINT64_C(9223372036854775808)));
    check(C_BI64_MAX, static_cast<::std::int64_t>(UINT64_C(9223372036854775807)));
    check(C_U8_MIN, static_cast<::std::uint8_t>(UINT8_C(0)));
    check(C_U8_MAX, static_cast<::std::uint8_t>(UINT8_C(255)));
    check(C_LU16_MIN, static_cast<::std::uint16_t>(UINT16_C(0)));
    check(C_LU16_MAX, static_cast<::std::uint16_t>(UINT16_C(65535)));
    check(C_LU32_MIN, static_cast<::std::uint32_t>(UINT32_C(0)));
    check(C_LU32_MAX, static_cast<::std::uint32_t>(UINT32_C(4294967295)));
    check(C_LU64_MIN, static_cast<::std::uint64_t>(UINT64_C(0)));
    check(C_LU64_MAX, static_cast<::std::uint64_t>(UINT64_C(18446744073709551615)));
    check(C_BU16_MIN, static_cast<::std::uint16_t>(UINT16_C(0)));
    check(C_BU16_MAX, static_cast<::std::uint16_t>(UINT16_C(65535)));
    check(C_BU32_MIN, static_cast<::std::uint32_t>(UINT32_C(0)));
    check(C_BU32_MAX, static_cast<::std::uint32_t>(UINT32_C(4294967295)));
    check(C_BU64_MIN, static_cast<::std::uint64_t>(UINT64_C(0)));
    check(C_BU64_MAX, static_cast<::std::uint64_t>(UINT64_C(18446744073709551615)));
}
