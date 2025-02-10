#pragma once

#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>
#include <initializer_list>
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
class SmallIntegerType {
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
    bool operator ==(const SmallIntegerType& _other) const {
        return contained == _other.contained;
    }
    bool operator !=(const SmallIntegerType& _other) const {
        return !(*this == _other);
    }
private:
};
class SmallIntegerTypeView {
public:
    static constexpr size_t SIZE_BYTES = 1;
    using Rendered = SmallIntegerTypeView;
    using Built = SmallIntegerType;
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
    explicit SmallIntegerTypeView(::gsl::span<const ::gsl::byte> _cons_buf) :_buf{ _cons_buf }{}
    ::gsl::span<const ::gsl::byte> _buf;
};
class MiniIntegerType {
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
    bool operator ==(const MiniIntegerType& _other) const {
        return contained == _other.contained;
    }
    bool operator !=(const MiniIntegerType& _other) const {
        return !(*this == _other);
    }
private:
};
class MiniIntegerTypeView {
public:
    static constexpr size_t SIZE_BYTES = 4;
    using Rendered = MiniIntegerTypeView;
    using Built = MiniIntegerType;
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
    explicit MiniIntegerTypeView(::gsl::span<const ::gsl::byte> _cons_buf) :_buf{ _cons_buf }{}
    ::gsl::span<const ::gsl::byte> _buf;
};
class ConfusingIntegerType {
public:
    using V = ::std::variant<::test_types::milestone1::MiniIntegerType, ::test_types::milestone1::SmallIntegerType>;
    V value;
    template <typename T, typename=typename ::std::enable_if<::std::is_constructible<V, T>::value, T>::type>
    ConfusingIntegerType(T&& t) : value{::std::forward<T>(t)} {}
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
            [](const ::test_types::milestone1::MiniIntegerType&) { return static_cast<::std::int8_t>(UINT8_C(0)); },
            [](const ::test_types::milestone1::SmallIntegerType&) { return static_cast<::std::int8_t>(UINT8_C(1)); }
        );
    }
    bool operator ==(const ::test_types::milestone1::ConfusingIntegerType& other) const {
        return value == other.value;
    }
    bool operator !=(const ::test_types::milestone1::ConfusingIntegerType& other) const {
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
class ConfusingIntegerTypeView {
public:
    using V = ::std::variant<::test_types::milestone1::MiniIntegerTypeView, ::test_types::milestone1::SmallIntegerTypeView>;
    V value;
    template <typename T, typename=typename ::std::enable_if<::std::is_constructible<V, T>::value, T>::type>
    ConfusingIntegerTypeView(T&& t) : value{::std::forward<T>(t)} {}
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
            [](const ::test_types::milestone1::MiniIntegerTypeView&) { return static_cast<::std::int8_t>(UINT8_C(0)); },
            [](const ::test_types::milestone1::SmallIntegerTypeView&) { return static_cast<::std::int8_t>(UINT8_C(1)); }
        );
    }
    using Rendered = ConfusingIntegerTypeView;
    static Rendered render(gsl::span<const gsl::byte> buf, ::std::int8_t tag) {
        if (tag == static_cast<::std::int8_t>(UINT8_C(0))) { return ::test_types::milestone1::MiniIntegerTypeView::render(buf); }
        if (tag == static_cast<::std::int8_t>(UINT8_C(1))) { return ::test_types::milestone1::SmallIntegerTypeView::render(buf); }
        throw ::std::domain_error("input had illegal value");
    }
    using Built = ::test_types::milestone1::ConfusingIntegerType;
    static Built build(const Rendered& rendered) {
        return rendered.match(
            [](const ::test_types::milestone1::MiniIntegerTypeView& x) -> Built { return ::test_types::milestone1::MiniIntegerTypeView::build(x); },
            [](const ::test_types::milestone1::SmallIntegerTypeView& x) -> Built { return ::test_types::milestone1::SmallIntegerTypeView::build(x); }
        );
    }
    Built build() const {
        return build(*this);
    }
    static ::tako::ParseResult<Rendered> parse(::gsl::span<const ::gsl::byte> buf, ::std::int8_t tag) {
        if (tag == static_cast<::std::int8_t>(UINT8_C(0))) {
            auto maybe = ::test_types::milestone1::MiniIntegerTypeView::parse(buf);
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
            auto maybe = ::test_types::milestone1::SmallIntegerTypeView::parse(buf);
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
class InnerVariant {
public:
    ::test_types::milestone1::ConfusingIntegerType inner;
    ::gsl::span<::gsl::byte> serialize_into(::gsl::span<::gsl::byte> buf) const {
        buf = ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::serialize_into(inner.tag(), buf);
        buf = ::test_types::milestone1::ConfusingIntegerTypeView::serialize_into(inner, buf);
        return buf;
    }
    using Buffer = ::std::vector<::gsl::byte>;
    size_t size_bytes() const {
        return 1 + ::test_types::milestone1::ConfusingIntegerTypeView::size_bytes(inner);
    }
    Buffer serialize() const {
        Buffer result{size_bytes()};
        serialize_into(result);
        return result;
    }
    bool operator ==(const InnerVariant& _other) const {
        return inner == _other.inner;
    }
    bool operator !=(const InnerVariant& _other) const {
        return !(*this == _other);
    }
private:
};
class InnerVariantView {
public:
    using Rendered = InnerVariantView;
    using Built = InnerVariant;
    static Built build(const Rendered& rendered) {
        return Built {
            .inner = ::test_types::milestone1::ConfusingIntegerTypeView::build(rendered.inner()),
        };
    }
    Built build() const {
        return build(*this);
    }
    static Rendered render(::gsl::span<const ::gsl::byte> _buf) {
        auto inner = ::test_types::milestone1::ConfusingIntegerTypeView::parse(::tako::unsafe_subspan(_buf, 1), ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::render(::tako::unsafe_subspan(_buf, 0))).value();
        return Rendered {
            _buf,
            ::std::move(inner)
        };
    }
    static ::tako::ParseResult<Rendered> parse(::gsl::span<const ::gsl::byte> _buf) {
        auto inner_injected_key_ = ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::parse(::tako::unsafe_subspan(_buf, 0));
        if (!inner_injected_key_) {
            return ::tl::make_unexpected(inner_injected_key_.error());
        }
        auto inner = ::test_types::milestone1::ConfusingIntegerTypeView::parse(::tako::unsafe_subspan(_buf, 1), inner_injected_key_->rendered);
        if (!inner) {
            return ::tl::make_unexpected(inner.error());
        }
        return ::tako::ParseResult<Rendered>(tl::in_place,
            Rendered {
                _buf,
                ::std::move(*inner)
            },
            ::tako::unsafe_subspan(inner->tail, 0)
        );
    }
    static gsl::span<gsl::byte> serialize_into(const Built& built, gsl::span<gsl::byte> buf) {
        return built.serialize_into(buf);
    }
    static size_t size_bytes(const Built& built) {
        return built.size_bytes();
    }
    ::gsl::span<const ::gsl::byte> raw_inner_injected_key_() const {
        return ::tako::unsafe_subspan(_buf, 0);
    }
    ::gsl::span<const ::gsl::byte> raw_inner() const {
        return ::tako::unsafe_subspan(_buf, 1);
    }
    ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::Rendered inner_injected_key_() const {
        return ::tako::PrimitiveView<::std::int8_t, ::tako::Endianness::LITTLE>::render(raw_inner_injected_key_());
    }
    ::test_types::milestone1::ConfusingIntegerTypeView::Rendered inner() const {
        return ::test_types::milestone1::ConfusingIntegerTypeView::render(raw_inner(), inner_injected_key_());
    }
    ::gsl::span<const ::gsl::byte> backing_buffer() const {
        return _buf;
    }
private:
    explicit InnerVariantView(::gsl::span<const ::gsl::byte> _cons_buf, ::tako::ParseInfo<::test_types::milestone1::ConfusingIntegerTypeView> _cons_info_inner) :_buf{ _cons_buf },_info_inner{ _cons_info_inner }{}
    ::gsl::span<const ::gsl::byte> _buf;
    ::tako::ParseInfo<::test_types::milestone1::ConfusingIntegerTypeView> _info_inner;
};
class Two {
public:
    using V = ::std::variant<::test_types::milestone1::IntegerType, ::test_types::milestone1::BigIntegerType, ::test_types::milestone1::InnerVariant>;
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
            [](const ::test_types::milestone1::BigIntegerType&) { return static_cast<::std::int8_t>(UINT8_C(1)); },
            [](const ::test_types::milestone1::InnerVariant&) { return static_cast<::std::int8_t>(UINT8_C(2)); }
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
    using V = ::std::variant<::test_types::milestone1::IntegerTypeView, ::test_types::milestone1::BigIntegerTypeView, ::test_types::milestone1::InnerVariantView>;
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
            [](const ::test_types::milestone1::BigIntegerTypeView&) { return static_cast<::std::int8_t>(UINT8_C(1)); },
            [](const ::test_types::milestone1::InnerVariantView&) { return static_cast<::std::int8_t>(UINT8_C(2)); }
        );
    }
    using Rendered = TwoView;
    static Rendered render(gsl::span<const gsl::byte> buf, ::std::int8_t tag) {
        if (tag == static_cast<::std::int8_t>(UINT8_C(0))) { return ::test_types::milestone1::IntegerTypeView::render(buf); }
        if (tag == static_cast<::std::int8_t>(UINT8_C(1))) { return ::test_types::milestone1::BigIntegerTypeView::render(buf); }
        if (tag == static_cast<::std::int8_t>(UINT8_C(2))) { return ::test_types::milestone1::InnerVariantView::render(buf); }
        throw ::std::domain_error("input had illegal value");
    }
    using Built = ::test_types::milestone1::Two;
    static Built build(const Rendered& rendered) {
        return rendered.match(
            [](const ::test_types::milestone1::IntegerTypeView& x) -> Built { return ::test_types::milestone1::IntegerTypeView::build(x); },
            [](const ::test_types::milestone1::BigIntegerTypeView& x) -> Built { return ::test_types::milestone1::BigIntegerTypeView::build(x); },
            [](const ::test_types::milestone1::InnerVariantView& x) -> Built { return ::test_types::milestone1::InnerVariantView::build(x); }
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
        if (tag == static_cast<::std::int8_t>(UINT8_C(2))) {
            auto maybe = ::test_types::milestone1::InnerVariantView::parse(buf);
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
class PacketView {
public:
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
