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

#include <array>
#include <algorithm>

namespace tako {

template <typename Enum>
struct EnumBound {
    typename Enum::Underlying min;
    typename Enum::Underlying max;
    constexpr size_t end() const {
        return encode(Enum::make_unsafe(max)) + 1;
    }
    constexpr size_t encode(Enum x) const {
        return static_cast<size_t>(x.value() - min);
    }
    constexpr Enum decode(size_t x) const {
        return Enum::make_unsafe(static_cast<typename Enum::Underlying>(x) + min);
    }
};
template <typename Enum>
constexpr EnumBound<Enum> find_enum_bound() {
    std::array<typename Enum::Underlying, Enum::VALUES.size()> values{};
    for (size_t i = 0; i < values.size(); i++) {
        values[i] = Enum::VALUES[i].value();
    }
    const auto [min, max] = std::minmax_element(values.begin(), values.end());
    return {
        .min = *min,
        .max = *max,
    };
}

}
