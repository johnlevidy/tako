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

#include <type_traits>
#include <limits>
#include <optional>
#include "tako/tako.hh"
#include "nlohmann/json.hpp"

namespace tako {

template <typename T>
struct PrimitiveJson {
    using Built = T;
    using JsonType = ::std::conditional_t<::std::is_signed_v<T>, int64_t, uint64_t>;
    static Result<Built> from_json(const nlohmann::json& j) {
        if (!j.is_number()) {
            return tl::make_unexpected(ParseError::MALFORMED);
        }
        auto value = j.get<JsonType>();
        if (value <= ::std::numeric_limits<T>::max() && value >= ::std::numeric_limits<T>::min()) {
            return static_cast<T>(value);
        } else {
            return tl::make_unexpected(ParseError::MALFORMED);
        }
    }
};

template <>
struct PrimitiveJson<float> {
    using Built = float;
    static Result<Built> from_json(const nlohmann::json& j) {
        if (!j.is_number()) {
            return tl::make_unexpected(ParseError::MALFORMED);
        }
        return j.get<float>();
    }
};

template <>
struct PrimitiveJson<double> {
    using Built = double;
    static Result<Built> from_json(const nlohmann::json& j) {
        if (!j.is_number()) {
            return tl::make_unexpected(ParseError::MALFORMED);
        }
        return j.get<double>();
    }
};

template <typename T, size_t N>
struct ArrayJson {
    using Built = ::std::array<typename T::Built, N>;
    static Result<Built> from_json(const nlohmann::json& j) {
        return from_json_inner(j, ::std::make_index_sequence<N>{});
    }
private:
    template <size_t... I>
    static Result<Built> from_json_inner(const nlohmann::json& j, ::std::index_sequence<I...>) {
        if (!j.is_array() || j.size() != N) {
            return tl::make_unexpected(ParseError::MALFORMED);
        }
        ::std::array<Result<typename T::Built>, N> inner{T::from_json(j[I])...};
        for (const auto& x : inner) {
            if (!x) {
                return tl::make_unexpected(x.error());
            }
        }
        return Built{*inner[I]...};
    }
};

template <typename T>
struct VectorJson {
    using Built = ::std::vector<typename T::Built>;
    static Result<Built> from_json(const nlohmann::json& j, size_t size) {
        if (!j.is_array() || j.size() != size) {
            return tl::make_unexpected(ParseError::MALFORMED);
        }
        Built result{};
        result.reserve(size);
        for (auto const& e : j) {
            auto parsed = T::from_json(e);
            if (!parsed) {
                return tl::make_unexpected(parsed.error());
            } else {
                result.push_back(*parsed);
            }
        }
        return result;
    }
};

}


