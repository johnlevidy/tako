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

#pragma once
#include <gsl.hpp>
#include <array>
#include <cstdint>
#include <algorithm>
#include <type_traits>
#include <tako/tako.hh>
#include "catch2/catch.hpp"

namespace tako {

template <typename... T>
auto byte_array(T... values) -> std::array<gsl::byte, sizeof...(values)> {
    return {gsl::byte{static_cast<uint8_t>(values)}...};
}

template <typename Actual, typename Expected>
void require_same() {
    STATIC_REQUIRE(std::is_same<typename std::decay<Actual>::type, Expected>::value);
}

template <typename T>
T expect_parse(tako::ParseResult<T> result) {
    REQUIRE(bool(result));
    return result->rendered;
}

template <typename T>
tako::ParseInfo<T> expect_parse_full(gsl::span<const gsl::byte> buf) {
    tako::ParseResult<T> result = T::parse(buf);
    REQUIRE(bool(result));
    return *result;
}

template <typename T>
T expect_parse(gsl::span<const gsl::byte> buf) {
    return expect_parse_full<T>(buf).rendered;
}

template <typename V, typename B>
void expect_parse_to(gsl::span<const gsl::byte> buf, B built) {
    CHECK(expect_parse<V>(buf).build() == built);
}

template <typename T>
tako::ParseError expect_parse_fail(gsl::span<const gsl::byte> buf) {
    tako::ParseResult<T> result = T::parse(buf);
    REQUIRE_FALSE(result);
    return result.error();
}

template <typename T1, typename T2>
bool buf_equals(const T1& t1, const T2& t2) {
    return std::equal(t1.begin(), t1.end(), t2.begin(), t2.end());
}

template <typename Data, typename Owned, typename View>
bool consistent(const Data& data, const Owned& owned, const View& view) {
    return buf_equals(data, owned.serialize()) && buf_equals(data, view.build().serialize());
}

inline std::vector<int8_t> make_string(const std::string& str) {
    std::vector<int8_t> result;
    std::copy(str.begin(), str.end(), std::back_inserter(result));
    return result;
}

template <typename T, typename V>
const T& expect_type(const V& v) {
    auto maybe = v.template get<T>();
    REQUIRE(maybe);
    return **maybe;
}

}
