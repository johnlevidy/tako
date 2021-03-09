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
#include <utility>
#include <algorithm>
#include <bitset>
#include <type_traits>
#include <climits>

#include "tako/enum_util.hh"

namespace tako {

template<typename KeyEnum>
class EnumSet {
private:
    static constexpr auto BOUND = find_enum_bound<KeyEnum>();
public:
    using bitset_type = std::bitset<BOUND.end()>;
    using key_type = KeyEnum;
    using value_type = KeyEnum;
    using size_type = size_t;
    using difference_type = ptrdiff_t;
    using reference = value_type&;
    using const_reference = const value_type&;
    using pointer = value_type*;
    using const_pointer = const value_type*;
    struct const_iterator {
        using difference_type = ptrdiff_t;
        using value_type = KeyEnum;
        using pointer = const KeyEnum*;
        using reference = KeyEnum&;
        using iterator_category = std::forward_iterator_tag;
        using self_type = const_iterator;

        const_iterator(const bitset_type& bits, size_t current_bit) :
            bits_{bits}, current_bit_(current_bit) {
            advance_to_set_bit();
        }

        self_type operator++(int) {
            self_type t = *this;
            ++*this;
            return t;
        }
        self_type const &operator++() {
            current_bit_++;
            advance_to_set_bit();
            return *this;
        }
        value_type operator*() const {
            return BOUND.decode(current_bit_);
        }
        struct pointer_proxy {
            KeyEnum x;
            const KeyEnum* operator->() const {
                return &x;
            }
        };
        pointer_proxy operator->() const {
            return pointer_proxy{**this};
        }
        bool operator==(self_type const &rhs) const {
            return current_bit_ == rhs.current_bit_;
        }
        bool operator!=(self_type const &rhs) const {
            return !(*this == rhs);
        }
    private:
        const bitset_type& bits_;
        size_t current_bit_;

        void advance_to_set_bit() {
            while(current_bit_ != bits_.size() && !bits_.test(current_bit_)) {
                current_bit_++;
            }
        }
    };
    using iterator = const_iterator;

    // The only constructor which is constexpr on a std::bitset takes an unsigned long long
    // Furthermore, if we are going to try to represent it as an unsigned long,
    // the minimum must be >= 0 and the max (not end()) has to be in range.
    // (Roughly, max < 63, as 63 is the highest bit)
    // The unsigned long representation uses an unshifted encoding
    // (An enum that spans from 64 to 127 can't be used, even though it would actually
    // fit.)
    static constexpr bool HAS_ULLONG_REPR =
        (BOUND.max < sizeof(unsigned long long) * CHAR_BIT) &&
        (BOUND.min >= static_cast<typename KeyEnum::Underlying>(0));
    // Internally, we use the most compressed representation possible,
    // by having the enum with value BOUND.min() stored at position 0
    // in the bitset. However, to take an external ULLONG,
    // where each enum is stored at the bit corresponding to its
    // value, and convert it to an internal ULLONG, we shift
    // right by ULLONG_EXTERNAL_SHIFT.
    static constexpr size_t ULLONG_EXTERNAL_SHIFT = BOUND.min;

    template <typename T=int>
    constexpr EnumSet(std::enable_if_t<HAS_ULLONG_REPR && std::is_same_v<T, int>, unsigned long long> val) :
        bitset_(val >> ULLONG_EXTERNAL_SHIFT) {};

    template <typename InputIt>
    constexpr EnumSet(InputIt begin, std::enable_if_t<HAS_ULLONG_REPR, InputIt> end) {
        unsigned long long mask = 0LLU;
        for (InputIt current = begin; current != end; ++current) {
            // Do not use BOUND.encode! Since we fit in a ullong,
            // to make this constexpr, build the set as an external bitset
            mask |= (1LLU << static_cast<size_t>(current->value()));
        }
        bitset_ = bitset_type{mask >> ULLONG_EXTERNAL_SHIFT};
    }

    template <typename InputIt>
    EnumSet(InputIt begin, std::enable_if_t<!HAS_ULLONG_REPR, InputIt> end) {
        insert(begin, end);
    }

    constexpr EnumSet() {}
    constexpr EnumSet(std::initializer_list<KeyEnum> x) :
        EnumSet(x.begin(), x.end()) {
    }

    iterator begin() const {
        return cbegin();
    }
    const_iterator cbegin() const {
        return const_iterator(bitset_, 0);
    }
    iterator end() const {
        return cend();
    }
    const_iterator cend() const {
        return const_iterator(bitset_, bitset_.size());
    }
    bool empty() const {
        return bitset_.none();
    }
    size_t size() const {
        return bitset_.count();
    }
    size_t max_size() const {
        return bitset_.size();
    }
    void clear() {
        bitset_.reset();
    }
    void insert(KeyEnum x) {
        bitset_.set(BOUND.encode(x));
    }
    template <typename InputIt>
    void insert(InputIt begin, InputIt end) {
        for (InputIt current = begin; current != end; ++current) {
            insert(*current);
        }
    }
    void erase(KeyEnum x) {
        bitset_.reset(BOUND.encode(x));
    }
    void erase(const_iterator pos) {
        erase(*pos);
    }
    void erase(const_iterator first, const_iterator last) {
        for (const_iterator current = first; current != last; ++current) {
            erase(current);
        }
    }
    constexpr bool contains(const KeyEnum& key) const {
        return bitset_[BOUND.encode(key)];
    }
    constexpr size_t count(const KeyEnum& key) const {
        return contains(key) ? 1 : 0;
    }
    const_iterator find(const KeyEnum& key) const {
        if (contains(key)) {
            return const_iterator(bitset_, BOUND.encode(key));
        } else {
            return end();
        }
    }
    std::pair<const_iterator, const_iterator> equal_range(const KeyEnum& key) const {
        auto result_begin = find(key);
        auto result_end = result_begin;
        if (result_end != end()) {
            result_end++;
        }
        return {result_begin, result_end};
    }
    // The template must depend on T for enable_if to work with SFINAE
    template <typename T=int>
    std::enable_if_t<HAS_ULLONG_REPR && std::is_same_v<int, T>, unsigned long long> to_ullong() const {
        return bitset_.to_ullong() << ULLONG_EXTERNAL_SHIFT;
    }
    bool operator==(const EnumSet<KeyEnum>& rhs) const {
        return bitset_ == rhs.bitset_;
    }
    bool operator!=(const EnumSet<KeyEnum>& rhs) const {
        return bitset_ != rhs.bitset_;
    }
private:
    bitset_type bitset_;
};

template<typename T>
constexpr auto make_enum_set() -> EnumSet<T> {
    return EnumSet<T>{};
}

template<typename... Ts>
constexpr auto make_enum_set(Ts&&... ts) -> EnumSet<std::common_type_t<Ts...>> {
    return EnumSet<std::common_type_t<Ts...>>{std::forward<Ts>(ts)...};
}

}
