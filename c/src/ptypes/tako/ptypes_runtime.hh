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

#include <string_view>
#include <limits>
#include "tako/ptypes.hh"
#include "tl/expected.hpp"

namespace tako {

/*
template <typename X, typename... T>
struct IsOneOf;

template <typename X, typename H, typename... T>
struct IsOneOf<X, H, T...> {
    static constexpr bool value = std::is_same<X, H> || IsOneOf<X, T...>;
};

template <typename X>
struct IsOneOf<X> {
    static constexpr bool value = false;
};
*/

template <typename X, typename... T>
inline constexpr bool is_one_of_v = (std::is_same_v<T, X> || ...);

template <typename X>
inline constexpr bool is_ptype_string_v = is_one_of_v<X, ptypes::StringL8, ptypes::StringL16, ptypes::StringL32>;

template <typename T>
tl::expected<T, Unit> make_ptype_string(const std::string_view& view) {
    // TODO: need to figure out what to do if the string is too long
    // That's why this returns an expected
    static_assert(is_ptype_string_v<T>, "T must be a ptype string");
    return T {
        .data = decltype(T::data){view.begin(), view.end()}
    };
}

template <typename T>
std::string_view make_string_view(const T& string_msg) {
    static_assert(is_ptype_string_v<T>, "T must be a ptype string");
    return std::string_view{
        reinterpret_cast<const char*>(string_msg.data.data()),
        string_msg.data.size()
    };
}

}
