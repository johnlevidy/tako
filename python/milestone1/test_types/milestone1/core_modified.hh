#pragma once

#include <iostream>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>
#include <initializer_list>
#include <cstddef>
#include <array>
#include <vector>
#include <variant>
#include <stdexcept>
#include <optional>
#include "tako/tako.hh"

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
namespace test_types {
namespace milestone1 {
class IntegerType {
public:
    ::std::int8_t contained;
    ::gsl::span<::gsl::byte> serialize_into(::gsl::span<::gsl::byte> buf) const {
        buf = ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::serialize_into(contained, buf);
        return buf;
    }
    static constexpr size_t SIZE_BYTES = 1;
    using Buffer = ::std::array<::gsl::byte, 1>;
    constexpr size_t size_bytes() const {
        return SIZE_BYTES;
    }
    Buffer serialize() const {
        Buffer result;
        serialize_into(result);
        return result;
    }
    bool operator ==(const IntegerType& _other) const {
        return contained == _other.contained;
    }
    bool operator !=(const IntegerType& _other) const {
        return !(*this == _other);
    }
private:
};
class IntegerTypeView {
public:
    static constexpr size_t SIZE_BYTES = 1;
    using Rendered = IntegerTypeView;
    using Built = IntegerType;
    static Built build(const Rendered& rendered) {
        return Built {
            .contained = ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::build(rendered.contained()),
        };
    }
    Built build() const {
        return build(*this);
    }
    static Rendered render(::gsl::span<const ::gsl::byte> _buf) {
        return Rendered {
            _buf
        };
    }
    static ::tako::ParseResult<Rendered> parse(::gsl::span<const ::gsl::byte> _buf) {
        if (::tako::unsafe_subspan(_buf, 1).data() > _buf.end()) {
            return ::tl::make_unexpected(::tako::ParseError::NOT_ENOUGH_DATA);
        }
        return ::tako::ParseResult<Rendered>(tl::in_place,
            Rendered {
                _buf
            },
            ::tako::unsafe_subspan(_buf, 1)
        );
    }
    static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
        return built.serialize_into(buf);
    }
    static size_t size_bytes(const Built& built) {
        return built.size_bytes();
    }
    ::gsl::span<const ::gsl::byte> raw_contained() const {
        return ::tako::unsafe_subspan(_buf, 0);
    }
    ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::Rendered contained() const {
        return ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::render(raw_contained());
    }
    ::gsl::span<const ::gsl::byte> backing_buffer() const {
        return _buf;
    }
private:
    explicit IntegerTypeView(::gsl::span<const ::gsl::byte> _cons_buf) :_buf{ _cons_buf }{}
    ::gsl::span<const ::gsl::byte> _buf;
};

class BigIntegerType {
public:
    ::std::int32_t contained;
    ::gsl::span<::gsl::byte> serialize_into(::gsl::span<::gsl::byte> buf) const {
        buf = ::tako::PrimitiveView<::std::int32_t, ::tako::Endianness::LITTLE>::serialize_into(contained, buf);
        return buf;
    }
    static constexpr size_t SIZE_BYTES = 4;
    using Buffer = ::std::array<::gsl::byte, 4>;
    constexpr size_t size_bytes() const {
        return SIZE_BYTES;
    }
    Buffer serialize() const {
        Buffer result;
        serialize_into(result);
        return result;
    }
    bool operator ==(const BigIntegerType& _other) const {
        return contained == _other.contained;
    }
    bool operator !=(const BigIntegerType& _other) const {
        return !(*this == _other);
    }
private:
};
class BigIntegerTypeView {
public:
    static constexpr size_t SIZE_BYTES = 4;
    using Rendered = BigIntegerTypeView;
    using Built = BigIntegerType;
    static Built build(const Rendered& rendered) {
        return Built {
            .contained = ::tako::PrimitiveView<::std::int32_t, ::tako::Endianness::LITTLE>::build(rendered.contained()),
        };
    }
    Built build() const {
        return build(*this);
    }
    static Rendered render(::gsl::span<const ::gsl::byte> _buf) {
        return Rendered {
            _buf
        };
    }
    static ::tako::ParseResult<Rendered> parse(::gsl::span<const ::gsl::byte> _buf) {
        if (::tako::unsafe_subspan(_buf, 4).data() > _buf.end()) {
            return ::tl::make_unexpected(::tako::ParseError::NOT_ENOUGH_DATA);
        }
        return ::tako::ParseResult<Rendered>(tl::in_place,
            Rendered {
                _buf
            },
            ::tako::unsafe_subspan(_buf, 4)
        );
    }
    static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
        return built.serialize_into(buf);
    }
    static size_t size_bytes(const Built& built) {
        return built.size_bytes();
    }
    ::gsl::span<const ::gsl::byte> raw_contained() const {
        return ::tako::unsafe_subspan(_buf, 0);
    }
    ::tako::PrimitiveView<::std::int32_t, ::tako::Endianness::LITTLE>::Rendered contained() const {
        return ::tako::PrimitiveView<::std::int32_t, ::tako::Endianness::LITTLE>::render(raw_contained());
    }
    ::gsl::span<const ::gsl::byte> backing_buffer() const {
        return _buf;
    }
private:
    explicit BigIntegerTypeView(::gsl::span<const ::gsl::byte> _cons_buf) :_buf{ _cons_buf }{}
    ::gsl::span<const ::gsl::byte> _buf;
};
class Two {
public:
    using V = ::std::variant<::test_types::milestone1::IntegerType, ::test_types::milestone1::BigIntegerType>;
    V value;
    template <typename T, typename=typename ::std::enable_if<::std::is_constructible<V, T>::value, T>::type>
    Two(T&& t) : value{::std::forward<T>(t)} {}
    template <typename... F>
    auto match(F&&... args) {
        return accept(::tako::overloaded{::std::forward<F>(args)...});
    }
    template <typename... F>
    auto match(F&&... args) const {
        return accept(::tako::overloaded{::std::forward<F>(args)...});
    }
    template <typename T>
    auto accept(T&& visitor) {
        return ::std::visit(::std::forward<T>(visitor), value);
    }
    template <typename T>
    auto accept(T&& visitor) const {
        return ::std::visit(::std::forward<T>(visitor), value);
    }
    template <typename R, typename... F>
    auto match_unify(F&&... args) {
        return accept_unify<R>(::tako::overloaded{::std::forward<F>(args)...});
    }
    template <typename R, typename... F>
    auto match_unify(F&&... args) const {
        return accept_unify<R>(::tako::overloaded{::std::forward<F>(args)...});
    }
    template <typename R, typename T>
    auto accept_unify(T&& visitor) {
        return ::std::visit(::tako::unify<R>(::std::forward<T>(visitor)), value);
    }
    template <typename R, typename T>
    auto accept_unify(T&& visitor) const {
        return ::std::visit(::tako::unify<R>(::std::forward<T>(visitor)), value);
    }
    template <typename T>
    ::std::optional<T*> get() {
        auto x = ::std::get_if<T>(&value);
        if (x) {
            return x;
        } else {
            return ::std::nullopt;
        }
    }
    template <typename T>
    ::std::optional<const T*> get() const {
        auto x = ::std::get_if<T>(&value);
        if (x) {
            return x;
        } else {
            return ::std::nullopt;
        }
    }
    ::std::int8_t tag() const {
        return match(
            [](const ::test_types::milestone1::IntegerType&) { return static_cast<::std::int8_t>(UINT8_C(0)); },
            [](const ::test_types::milestone1::BigIntegerType&) { return static_cast<::std::int8_t>(UINT8_C(1)); }
        );
    }
    bool operator ==(const ::test_types::milestone1::Two& other) const {
        return value == other.value;
    }
    bool operator !=(const ::test_types::milestone1::Two& other) const {
        return value != other.value;
    }
    gsl::span<gsl::byte> serialize_into(gsl::span<gsl::byte> buf) const {
        return accept([&buf](auto&& x){
            return x.serialize_into(buf);
        });
    }
    size_t size_bytes() const {
        return accept([](auto&& x){
            return x.size_bytes();
        });
    }
};
class TwoView {
public:
    using V = ::std::variant<::test_types::milestone1::IntegerTypeView, ::test_types::milestone1::BigIntegerTypeView>;
    V value;
    template <typename T, typename=typename ::std::enable_if<::std::is_constructible<V, T>::value, T>::type>
    TwoView(T&& t) : value{::std::forward<T>(t)} {}
    template <typename... F>
    auto match(F&&... args) {
        return accept(::tako::overloaded{::std::forward<F>(args)...});
    }
    template <typename... F>
    auto match(F&&... args) const {
        return accept(::tako::overloaded{::std::forward<F>(args)...});
    }
    template <typename T>
    auto accept(T&& visitor) {
        return ::std::visit(::std::forward<T>(visitor), value);
    }
    template <typename T>
    auto accept(T&& visitor) const {
        return ::std::visit(::std::forward<T>(visitor), value);
    }
    template <typename R, typename... F>
    auto match_unify(F&&... args) {
        return accept_unify<R>(::tako::overloaded{::std::forward<F>(args)...});
    }
    template <typename R, typename... F>
    auto match_unify(F&&... args) const {
        return accept_unify<R>(::tako::overloaded{::std::forward<F>(args)...});
    }
    template <typename R, typename T>
    auto accept_unify(T&& visitor) {
        return ::std::visit(::tako::unify<R>(::std::forward<T>(visitor)), value);
    }
    template <typename R, typename T>
    auto accept_unify(T&& visitor) const {
        return ::std::visit(::tako::unify<R>(::std::forward<T>(visitor)), value);
    }
    template <typename T>
    ::std::optional<T*> get() {
        auto x = ::std::get_if<T>(&value);
        if (x) {
            return x;
        } else {
            return ::std::nullopt;
        }
    }
    template <typename T>
    ::std::optional<const T*> get() const {
        auto x = ::std::get_if<T>(&value);
        if (x) {
            return x;
        } else {
            return ::std::nullopt;
        }
    }
    ::std::int8_t tag() const {
        return match(
            [](const ::test_types::milestone1::IntegerTypeView&) { return static_cast<::std::int8_t>(UINT8_C(0)); },
            [](const ::test_types::milestone1::BigIntegerTypeView&) { return static_cast<::std::int8_t>(UINT8_C(1)); }
        );
    }
    using Rendered = TwoView;
    static Rendered render(gsl::span<const gsl::byte> buf, ::std::int8_t tag) {
        if (tag == static_cast<::std::int8_t>(UINT8_C(0))) { return ::test_types::milestone1::IntegerTypeView::render(buf); }
        if (tag == static_cast<::std::int8_t>(UINT8_C(1))) { return ::test_types::milestone1::BigIntegerTypeView::render(buf); }
        throw ::std::domain_error("input had illegal value");
    }
    using Built = ::test_types::milestone1::Two;
    static Built build(const Rendered& rendered) {
        return rendered.match(
            [](const ::test_types::milestone1::IntegerTypeView& x) -> Built { return ::test_types::milestone1::IntegerTypeView::build(x); },
            [](const ::test_types::milestone1::BigIntegerTypeView& x) -> Built { return ::test_types::milestone1::BigIntegerTypeView::build(x); }
        );
    }
    Built build() const {
        return build(*this);
    }
    static ::tako::ParseResult<Rendered> parse(::gsl::span<const ::gsl::byte> buf, ::std::int8_t tag) {
        if (tag == static_cast<::std::int8_t>(UINT8_C(0))) {
            auto maybe = ::test_types::milestone1::IntegerTypeView::parse(buf);
            if (!maybe) {
                return tl::make_unexpected(maybe.error());
            } else {
                return ::tako::ParseResult<Rendered>(tl::in_place,
                    ::std::move(maybe->rendered),
                    maybe->tail
                );
            }
        }
        if (tag == static_cast<::std::int8_t>(UINT8_C(1))) {
            auto maybe = ::test_types::milestone1::BigIntegerTypeView::parse(buf);
            if (!maybe) {
                return tl::make_unexpected(maybe.error());
            } else {
                return ::tako::ParseResult<Rendered>(tl::in_place,
                    ::std::move(maybe->rendered),
                    maybe->tail
                );
            }
        }
        return ::tl::make_unexpected(::tako::ParseError::MALFORMED);
    }
    static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
        return built.serialize_into(buf);
    }
    static size_t size_bytes(const Built& built) {
        return built.size_bytes();
    }
};
class Packet {
public:
    ::std::int32_t one;
    ::test_types::milestone1::Two two;
    ::std::uint32_t three;
    ::gsl::span<::gsl::byte> serialize_into(::gsl::span<::gsl::byte> buf) const {
        buf = ::tako::PrimitiveView<::std::int32_t, ::tako::Endianness::LITTLE>::serialize_into(one, buf);
        buf = ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::serialize_into(two.tag(), buf);
        buf = ::test_types::milestone1::TwoView::serialize_into(two, buf);
        buf = ::tako::PrimitiveView<::std::uint32_t, ::tako::Endianness::LITTLE>::serialize_into(three, buf);
        return buf;
    }
    using Buffer = ::std::vector<::gsl::byte>;
    size_t size_bytes() const {
        return 9 + ::test_types::milestone1::TwoView::size_bytes(two);
    }
    Buffer serialize() const {
        Buffer result{size_bytes()};
        serialize_into(result);
        return result;
    }
    bool operator ==(const Packet& _other) const {
        return one == _other.one && two == _other.two && three == _other.three;
    }
    bool operator !=(const Packet& _other) const {
        return !(*this == _other);
    }
private:
};
class PacketPeek {
public:
    explicit PacketPeek(::gsl::span<const ::gsl::byte> _cons_buf, ::tako::ParseResult<::test_types::milestone1::TwoView> _cons_info_two, size_t _good_bytes) :_buf{ _cons_buf },_info_two{ _cons_info_two },good_bytes{ _good_bytes }{}
    ::gsl::span<const ::gsl::byte> _buf;
    ::tako::ParseResult<::test_types::milestone1::TwoView> _info_two;
    size_t good_bytes;
};
class PacketView {
public:
    using Peek = PacketPeek;
    using Rendered = PacketView;
    using Built = Packet;
    static Built build(const Rendered& rendered) {
        return Built {
            .one = ::tako::PrimitiveView<::std::int32_t, ::tako::Endianness::LITTLE>::build(rendered.one()),
            .two = ::test_types::milestone1::TwoView::build(rendered.two()),
            .three = ::tako::PrimitiveView<::std::uint32_t, ::tako::Endianness::LITTLE>::build(rendered.three()),
        };
    }
    Built build() const {
        return build(*this);
    }


    // Basically the same as parse so far
    static Peek peek(::gsl::span<const ::gsl::byte> _buf) {
        // For every simple field, do something like this:
        // Distinct case from parse, we have to check every field.
        // parse assumes it's fine to just check the next one because if that one
        // is bad this one certainly is, if it's good this one is
        if (::tako::unsafe_subspan(_buf, 4).data() > _buf.end()) {
            return Peek { _buf, tl::make_unexpected(::tako::ParseError::MALFORMED), 0 };
        }
        // For complex fields, we have to try to parse
        auto two_injected_key_ = ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::parse(::tako::unsafe_subspan(_buf, 4));
        if (!two_injected_key_) {
            return Peek { _buf, tl::make_unexpected(::tako::ParseError::MALFORMED), 4 };
        }
        // We grabbed the i8 type ID, now we grab the rest
        auto two = ::test_types::milestone1::TwoView::parse(::tako::unsafe_subspan(_buf, 5), two_injected_key_->rendered);
        if (!two) {
            return Peek { _buf, tl::make_unexpected(::tako::ParseError::MALFORMED), 4 };
        }
        // Check for data at the end
        if (::tako::unsafe_subspan(two->tail, 4).data() > _buf.end()) {
            return Peek { _buf, tl::make_unexpected(::tako::ParseError::MALFORMED), two->tail.data() - _buf.begin()};
        }
        return Peek { _buf, tl::make_unexpected(::tako::ParseError::MALFORMED), ::tako::unsafe_subspan(two->tail, 4).data() - _buf.begin()};
    }


    static Rendered render(::gsl::span<const ::gsl::byte> _buf) {
        auto two = ::test_types::milestone1::TwoView::parse(::tako::unsafe_subspan(_buf, 5), ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::render(::tako::unsafe_subspan(_buf, 4))).value();
        return Rendered {
            _buf,
            ::std::move(two)
        };
    }

    static ::tako::ParseResult<Rendered> parse(::gsl::span<const ::gsl::byte> _buf) {
        auto two_injected_key_ = ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::parse(::tako::unsafe_subspan(_buf, 4));
        if (!two_injected_key_) {
            return ::tl::make_unexpected(two_injected_key_.error());
        }
        auto two = ::test_types::milestone1::TwoView::parse(::tako::unsafe_subspan(_buf, 5), two_injected_key_->rendered);
        if (!two) {
            return ::tl::make_unexpected(two.error());
        }
        if (::tako::unsafe_subspan(two->tail, 4).data() > _buf.end()) {
            return ::tl::make_unexpected(::tako::ParseError::NOT_ENOUGH_DATA);
        }
        return ::tako::ParseResult<Rendered>(tl::in_place,
            Rendered {
                _buf,
                ::std::move(*two)
            },
            ::tako::unsafe_subspan(two->tail, 4)
        );
    }
    static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
        return built.serialize_into(buf);
    }
    static size_t size_bytes(const Built& built) {
        return built.size_bytes();
    }
    ::gsl::span<const ::gsl::byte> raw_one() const {
        return ::tako::unsafe_subspan(_buf, 0);
    }
    ::gsl::span<const ::gsl::byte> raw_two_injected_key_() const {
        return ::tako::unsafe_subspan(_buf, 4);
    }
    ::gsl::span<const ::gsl::byte> raw_two() const {
        return ::tako::unsafe_subspan(_buf, 5);
    }
    ::gsl::span<const ::gsl::byte> raw_three() const {
        return ::tako::unsafe_subspan(_info_two.tail, 0);
    }
    ::tako::PrimitiveView<::std::int32_t, ::tako::Endianness::LITTLE>::Rendered one() const {
        return ::tako::PrimitiveView<::std::int32_t, ::tako::Endianness::LITTLE>::render(raw_one());
    }
    ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::Rendered two_injected_key_() const {
        return ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::render(raw_two_injected_key_());
    }
    ::test_types::milestone1::TwoView::Rendered two() const {
        return ::test_types::milestone1::TwoView::render(raw_two(), two_injected_key_());
    }
    ::tako::PrimitiveView<::std::uint32_t, ::tako::Endianness::LITTLE>::Rendered three() const {
        return ::tako::PrimitiveView<::std::uint32_t, ::tako::Endianness::LITTLE>::render(raw_three());
    }
    ::gsl::span<const ::gsl::byte> backing_buffer() const {
        return _buf;
    }
private:
    explicit PacketView(::gsl::span<const ::gsl::byte> _cons_buf, ::tako::ParseInfo<::test_types::milestone1::TwoView> _cons_info_two) :_buf{ _cons_buf },_info_two{ _cons_info_two }{}
    ::gsl::span<const ::gsl::byte> _buf;
    ::tako::ParseInfo<::test_types::milestone1::TwoView> _info_two;
};
}
}
#pragma GCC diagnostic pop
