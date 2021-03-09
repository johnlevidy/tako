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

#include "test_types/bakery.hh"
#include "test_types/bakery/v1.hh"
#include "test_types/bakery/v2.hh"
#include "test_types/bakery/v3.hh"
#include "test_types/bakery/v4.hh"

using namespace test_types::bakery;
namespace v1 = test_types::bakery::v1;
namespace v2 = test_types::bakery::v2;
namespace v3 = test_types::bakery::v3;
namespace v4 = test_types::bakery::v4;
namespace latest = v4;
using namespace std;

// =====================================================
// BAKERY
// Operates on only the latest version
uint8_t flavor_id(const latest::Flavor& flavor) {
    if (flavor == latest::Flavor::VANILLA) { return 0; }
    if (flavor == latest::Flavor::CHOCOLATE) { return 63; }
    if (flavor == latest::Flavor::CARMEL) { return 94; }
    throw std::domain_error("input had illegal value");
}

latest::Message process_latest(const latest::MessageView& msg) {
    return latest::Message { .msg =  msg.msg().match(
        [&](const latest::ErrorResponseView&) -> latest::MessageVariant {
            return latest::ErrorResponse{};
        },
        [&](const latest::NewOrderRequestView& new_order_request) -> latest::MessageVariant {
            uint64_t order_id = new_order_request.order().match(
                [&](const latest::CupcakeOrderView& order) -> uint64_t {
                    // Very clever order ID system -- it works as long as you don't get
                    // the same order twice
                    uint64_t temp = static_cast<uint32_t>(order.quantity());
                    temp |= static_cast<uint64_t>(flavor_id(order.flavor())) << 32;
                    temp |= static_cast<uint64_t>(flavor_id(order.frosting_flavor())) << 40;
                    return temp;
                },
                [&](const latest::CakeOrderView&) -> uint64_t {
                    return 42;
                }
            );

            return latest::NewOrderResponse{.order_id = order_id};
        },
        [&](const latest::NewOrderResponseView&) -> latest::MessageVariant {
            return latest::ErrorResponse{};
        },
        [&](const latest::CancelOrderRequestView&) -> latest::MessageVariant {
            return latest::CancelOrderResponse{};
        },
        [&](const latest::CancelOrderResponseView&) -> latest::MessageVariant {
            return latest::ErrorResponse{};
        }
    )};
}

// =====================================================
// VERSION HANDLING
// Reads packets, converts them to the latest version, and then downgrades the output
class PacketVariantVisitor {
public:
    v1::Message operator()(const v1::MessageView& msg) const {
        // Added a field so this is a bit tricky, we have to copy it and build a new view
        auto next_bytes = v2::convert(msg.build(), tako::Type<v2::Message>{}).serialize();
        auto next_view = v2::MessageView::parse(next_bytes).value().rendered;
        return v2::convert((*this)(next_view), tako::Type<v1::Message>{});
    }
    v2::Message operator()(const v2::MessageView& msg) const {
        // Direct view-to-view conversion since we made a backwards compatible change
        // (adding Flavor::CARMEL)
        auto next_view = v3::convert(msg, tako::Type<v3::MessageView>{});
        return v3::convert((*this)(next_view), tako::Type<v2::Message>{});
    }
    v3::Message operator()(const v3::MessageView& msg) const {
        // Direct view-to-view conversion since we made a backwards compatible change
        // (adding messages types: CancelOrderRequest and CancelOrderResponse)
        auto next_view = v4::convert(msg, tako::Type<v4::MessageView>{});
        // Note that when we down-convert, there is a .value() -- the convert returns
        // an optional, because we added cancel order messages, and those can't
        // be represented in the prior version.
        return v4::convert((*this)(next_view), tako::Type<v3::Message>{}).value();
    }
    v4::Message operator()(const v4::MessageView& msg) const {
        return process_latest(msg);
    }
};

// =====================================================
// ENTRYPOINT

// Handles a new cupcake order and generates the response!
static std::vector<gsl::byte> handle_order(gsl::span<const gsl::byte> data) {
    tako::ParseResult<PacketView> parse_result = PacketView::parse(data);
    if (!parse_result) {
        return Packet {.payload = latest::Message {.msg = latest::ErrorResponse{}}}.serialize();
    }

    // Now we have a valid message, so we can process the order!
    PacketVariantView packet_variant = parse_result->rendered.payload();
    return Packet {
        .payload = packet_variant.accept(tako::unify<PacketVariant>(PacketVariantVisitor{})),
    }.serialize();
}
