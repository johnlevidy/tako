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

#include <cstring>
#include <type_traits>
#include <vector>
#include <endian.h>
#include <gsl.hpp>
#include <optional>
#include "tl/expected.hpp"

namespace tako {

template <typename T>
struct ParseInfo {
    ParseInfo(T r, gsl::span<const gsl::byte> t): rendered{std::move(r)}, tail{t} {};
    ParseInfo(ParseInfo const&) = default;
    ParseInfo(ParseInfo&&) = default;

    T rendered;
    gsl::span<const gsl::byte> tail;
};

enum class ParseError {
    MALFORMED,
    NOT_ENOUGH_DATA,
};

template <typename T>
using Result = tl::expected<T, ParseError>;

template <typename T>
using ParseResult = Result<ParseInfo<T>>;

template <typename T>
struct Type{};

enum class Endianness : uint8_t {
    BIG, LITTLE
};

// EndiannessToHost<T, E>, for all integral types T,
// provides a function T convert(T x) which converts the value in x from
// endianness E to the host endianness
template <typename T, Endianness E> struct EndiannessToHost;
template <Endianness E> struct EndiannessToHost<uint8_t, E> {
    static uint8_t convert(uint8_t x) { return x; }
};
template <> struct EndiannessToHost<uint16_t, Endianness::BIG> {
    static uint16_t convert(uint16_t x) { return be16toh(x); }
};
template <> struct EndiannessToHost<uint16_t, Endianness::LITTLE> {
    static uint16_t convert(uint16_t x) { return le16toh(x); }
};
template <> struct EndiannessToHost<uint32_t, Endianness::BIG> {
    static uint32_t convert(uint32_t x) { return be32toh(x); }
};
template <> struct EndiannessToHost<uint32_t, Endianness::LITTLE> {
    static uint32_t convert(uint32_t x) { return le32toh(x); }
};
template <> struct EndiannessToHost<uint64_t, Endianness::BIG> {
    static uint64_t convert(uint64_t x) { return be64toh(x); }
};
template <> struct EndiannessToHost<uint64_t, Endianness::LITTLE> {
    static uint64_t convert(uint64_t x) { return le64toh(x); }
};

// HostToEndianness<T, E>, for all integral types T,
// provides a function T convert(T x) which converts the value in x from
// the host endianness tot he endianness E
template <typename T, Endianness E> struct HostToEndianness;
template <Endianness E> struct HostToEndianness<uint8_t, E> {
    static uint8_t convert(uint8_t x) { return x; }
};
template <> struct HostToEndianness<uint16_t, Endianness::BIG> {
    static uint16_t convert(uint16_t x) { return htobe16(x); }
};
template <> struct HostToEndianness<uint16_t, Endianness::LITTLE> {
    static uint16_t convert(uint16_t x) { return htole16(x); }
};
template <> struct HostToEndianness<uint32_t, Endianness::BIG> {
    static uint32_t convert(uint32_t x) { return htobe32(x); }
};
template <> struct HostToEndianness<uint32_t, Endianness::LITTLE> {
    static uint32_t convert(uint32_t x) { return htole32(x); }
};
template <> struct HostToEndianness<uint64_t, Endianness::BIG> {
    static uint64_t convert(uint64_t x) { return htobe64(x); }
};
template <> struct HostToEndianness<uint64_t, Endianness::LITTLE> {
    static uint64_t convert(uint64_t x) { return htole64(x); }
};

// From https://en.cppreference.com/w/cpp/numeric/bit_cast
template <class To, class From>
typename std::enable_if_t<
    sizeof(To) == sizeof(From) &&
    std::is_trivially_copyable_v<From> &&
    std::is_trivially_copyable_v<To>,
    To
>
bit_cast(const From& src) noexcept {
    static_assert(std::is_trivially_constructible_v<To>,
        "This implementation additionally requires destination type to be trivially constructible");
    To dst;
    std::memcpy(&dst, &src, sizeof(To));
    return dst;
}

template <typename T>
gsl::span<T> unsafe_subspan(gsl::span<T> buf, size_t offset, size_t len) {
    // The same effect as this:
    //     return gsl::span<T>{buf.data() + offset, len};
    // But without bounds checks
    struct Container {
        T* data_;
        size_t size_;
        T* data() const { return data_; }
        size_t size() const { return size_; }
    };
    Container cont{buf.data() + offset, len};
    return gsl::span<T>{cont};
}
template <typename T>
gsl::span<T> unsafe_subspan(gsl::span<T> buf, size_t offset) {
    return unsafe_subspan(buf, offset, buf.size() - offset);
}

inline gsl::span<const gsl::byte> span_get(gsl::span<const gsl::byte> buf, size_t offset, size_t len) {
    return unsafe_subspan(buf, offset, len);
}

template <typename T>
T span_get(gsl::span<const gsl::byte> buf, size_t offset) {
    T result;
    std::memcpy(&result, unsafe_subspan(buf, offset).data(), sizeof(T));
    return result;
}

template <size_t E>
gsl::span<const gsl::byte> span_get_vector(gsl::span<const gsl::byte> buf, size_t idx) {
    return span_get(buf, idx * E, E);
}

template <typename T>
gsl::span<gsl::byte> span_put(T thing, gsl::span<gsl::byte> buf) {
    std::memcpy(buf.data(), &thing, sizeof(thing));
    return unsafe_subspan(buf, sizeof(thing));
}

template <typename T>
struct UintType {
    using type = typename std::make_unsigned<T>::type;
};

template <>
struct UintType<float> {
    static_assert(sizeof(float) == sizeof(uint32_t));
    using type = uint32_t;
};

template <>
struct UintType<double> {
    static_assert(sizeof(double) == sizeof(uint64_t));
    using type = uint64_t;
};

template <typename Output, Endianness E>
struct PrimitiveConverter {
    // The input type is the unsigned version -- the endianness conversion functions require and unsigned type
    using Input = typename UintType<Output>::type;

    static Output from_network(Input x) {
        x = EndiannessToHost<Input, E>::convert(x);
        Output out;
        std::memcpy(&out, &x, sizeof(out));
        return out;
    }

    static Output from_network(gsl::span<const gsl::byte> buf) {
        Input x = EndiannessToHost<Input, E>::convert(span_get<Input>(buf, 0));
        Output out;
        std::memcpy(&out, &x, sizeof(out));
        return out;
    }

    static Input to_network(Output x) {
        Input in;
        std::memcpy(&in, &x, sizeof(in));
        in = HostToEndianness<Input, E>::convert(in);
        return in;
    }

    static gsl::span<gsl::byte> to_network(Output x, gsl::span<gsl::byte> buf) {
        Input in;
        std::memcpy(&in, &x, sizeof(in));
        return span_put(HostToEndianness<Input, E>::convert(in), buf);
    }
};

template <typename Output, Endianness E>
class PrimitiveView {
public:
    using Converter = PrimitiveConverter<Output, E>;
    using Input = typename Converter::Input;

    static constexpr size_t SIZE_BYTES = sizeof(Output);

    using Rendered = Output;
    static Rendered render(gsl::span<const gsl::byte> buf) {
        return Converter::from_network(buf);
    }
    using Built = Output;
    static Built build(const Rendered& rendered) {
        return rendered;
    }

    static ParseResult<Rendered> parse(gsl::span<const gsl::byte> buf) {
        // This generates much better code that using buf.size()
        //    if (buf.size() < sizeof(Input))
        // This is because buf.size() causes a subtraction to occur
        // as spans are internally 2 pointers, not a pointer and a length
        auto tail = unsafe_subspan(buf, sizeof(Input));
        if (tail.data() > buf.end()) {
            return tl::make_unexpected(ParseError::NOT_ENOUGH_DATA);
        } else {
            return ParseResult<Rendered>(tl::in_place, render(buf), tail);
        }
    }

    static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
        return Converter::to_network(built, buf);
    }
    static constexpr size_t size_bytes(const Built&) {
        return SIZE_BYTES;
    }
};

template <typename T>
inline Result<gsl::span<const gsl::byte>> parse_vector(gsl::span<const gsl::byte> buf, size_t size) {
    for (size_t i = 0; i < size; i++) {
        auto inner_result = T::parse(buf);
        if (!inner_result) {
            return tl::make_unexpected(inner_result.error());
        } else {
            buf = inner_result->tail;
        }
    }
    return buf;
}

template <typename T, typename Rendered>
inline std::vector<typename T::Built> build_vector(const Rendered& rendered) {
    std::vector<typename T::Built> result{};
    result.reserve(rendered.size());
    for (size_t i = 0; i < rendered.size(); i++) {
        result.push_back(T::build(rendered[i]));
    }
    return result;
}

template <typename T, typename Built>
inline gsl::span<gsl::byte> serialize_into_vector(const Built& built, gsl::span<gsl::byte> buf) {
    for (size_t i = 0; i < built.size(); i++) {
        buf = T::serialize_into(built[i], buf);
    }
    return buf;
}

template <typename T>
class VectorView {
public:
    using value_type = typename T::Rendered;

    using Rendered = VectorView<T>;
    static Rendered render(gsl::span<const gsl::byte> buf, size_t size) {
        return Rendered{buf, size};
    }

    using Built = std::vector<typename T::Built>;
    static Built build(const Rendered& rendered) {
        Built result{};
        result.reserve(rendered.size());
        for (size_t i = 0; i < rendered.size(); i++) {
            result.push_back(T::build(rendered[i]));
        }
        return result;
    }

    static ParseResult<Rendered> parse(gsl::span<const gsl::byte> buf, size_t size) {
        auto result = parse_vector<T>(buf, size);
        if (!result) {
            return tl::make_unexpected(result.error());
        } else {
            return ParseResult<Rendered>(tl::in_place, render(buf, size), *result);
        }
    }

    static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
        return serialize_into_vector<T>(built, buf);
    }
    static size_t size_bytes(const Built& built) {
        return T::SIZE_BYTES * built.size();
    }

    typename T::Rendered operator[](size_t idx) const {
        return T::render(span_get_vector<T::SIZE_BYTES>(buf_, idx));
    }
    size_t size() const {
        return size_;
    }

private:
    VectorView(gsl::span<const gsl::byte> buf, size_t size) : buf_{buf}, size_{size} {}
    gsl::span<const gsl::byte> buf_;
    size_t size_;
};

template <typename T, size_t N>
class ArrayView {
public:
    using value_type = typename T::Rendered;
    static constexpr size_t SIZE_BYTES = T::SIZE_BYTES * N;

    using Rendered = ArrayView<T, N>;
    static Rendered render(gsl::span<const gsl::byte> buf) {
        return Rendered{buf};
    }

    using Built = std::array<typename T::Built, N>;
    static Built build(const Rendered& rendered) {
        return build(rendered, std::make_index_sequence<N>{});
    }

    static ParseResult<Rendered> parse(gsl::span<const gsl::byte> buf) {
        auto result = parse_vector<T>(buf, N);
        if (!result) {
            return tl::make_unexpected(result.error());
        } else {
            return ParseResult<Rendered>(tl::in_place, render(buf), *result);
        }
    }

    static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
        return serialize_into_vector<T>(built, buf);
    }
    static constexpr size_t size_bytes(const Built&) {
        return T::SIZE_BYTES * N;
    }

    typename T::Rendered operator[](size_t idx) const {
        return T::render(span_get_vector<T::SIZE_BYTES>(buf_, idx));
    }
    constexpr size_t size() const {
        return N;
    }

private:
    template <size_t... I>
    static Built build(const Rendered& rendered, std::index_sequence<I...>) {
        return Built{T::build(rendered[I])...};
    }

    ArrayView(gsl::span<const gsl::byte> buf) : buf_{buf} {}
    gsl::span<const gsl::byte> buf_;
};

template <typename T>
class ListView {
public:
    using value_type = typename T::Rendered;

    using Rendered = ListView<T>;
    static Rendered render(gsl::span<const gsl::byte> buf, size_t size) {
        return parse(buf, size).value().rendered;
    }

    using Built = std::vector<typename T::Built>;
    static Built build(const Rendered& rendered) {
        return build_vector<T, Rendered>(rendered);
    }

    static ParseResult<Rendered> parse(gsl::span<const gsl::byte> buf, size_t size) {
        std::vector<typename T::Rendered> parts;
        parts.reserve(size);
        for (size_t i = 0; i < size; i++) {
            auto maybe = T::parse(buf);
            if (!maybe) {
                return tl::make_unexpected(maybe.error());
            } else {
                parts.push_back(std::move(maybe->rendered));
                buf = maybe->tail;
            }
        }
        return ParseResult<Rendered>(tl::in_place, Rendered{std::move(parts)}, buf);
    }

    static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
        return serialize_into_vector<T>(built, buf);
    }
    static size_t size_bytes(const Built& built) {
        size_t result = 0;
        for (size_t i = 0; i < built.size(); i++) {
            result += T::size_bytes(built[i]);
        }
        return result;
    }

    typename T::Rendered operator[](size_t idx) const {
        return parts_[idx];
    }
    size_t size() const {
        return parts_.size();
    }

private:
    ListView(std::vector<typename T::Rendered> parts) : parts_{std::move(parts)} {}
    std::vector<typename T::Rendered> parts_;
};

// From the example at https://en.cppreference.com/w/cpp/utility/variant/visit
template<class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template<class... Ts> overloaded(Ts...) -> overloaded<Ts...>;

template<typename R, typename V>
struct Unified {
    V visitor;

    template <typename... T>
    R operator() (T&&... args) {
        return visitor(std::forward<T>(args)...);
    }
    template <typename... T>
    R operator() (T&&... args) const {
        return visitor(std::forward<T>(args)...);
    }
};
template <typename R, typename V>
Unified<R, V> unify(V&& v) {
    return Unified<R, V>{std::forward<V>(v)};
}

struct Unit {};
}

