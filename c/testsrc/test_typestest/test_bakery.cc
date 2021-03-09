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
#include "bakery.hh"
#include <iostream>

void test(Packet request, Packet expected_response) {
    std::vector<gsl::byte> request_bytes = request.serialize();
    std::vector<gsl::byte> response = handle_order(request_bytes);
    auto parsed = tako::expect_parse<PacketView>(response);
    CHECK(expected_response == parsed.build());

}

TEST_CASE("bakery_cake_order_v1") {
    test(
        Packet {
            .payload = v1::Message {
                .msg = v1::NewOrderRequest {
                    .name = {0, 1, 2, 3, 4},
                    .order = v1::CakeOrder {
                        .layers = 900,
                        .shape = v1::Shape::ROUND,
                        .flavor = v1::Flavor::CHOCOLATE,
                    },
                },
            },
        },
        Packet {
            .payload = v1::Message {
                .msg = v1::NewOrderResponse {
                    .order_id = 42,
                },
            },
        }
    );
}

TEST_CASE("bakery_cupcake_order_v1") {
    test(
        Packet {
            .payload = v1::Message {
                .msg = v1::NewOrderRequest {
                    .name = {0, 1, 2, 3, 4},
                    .order = v1::CupcakeOrder {
                        .quantity = 0x900,
                        .flavor = v1::Flavor::CHOCOLATE,
                    },
                },
            },
        },
        Packet {
            .payload = v1::Message {
                .msg = v1::NewOrderResponse {
                    .order_id = 0x0000003f00000900,
                },
            },
        }
    );
}

TEST_CASE("bakery_cake_order_v2") {
    test(
        Packet {
            .payload = v2::Message {
                .msg = v2::NewOrderRequest {
                    .name = {0, 1, 2, 3, 4},
                    .order = v2::CakeOrder {
                        .layers = 900,
                        .shape = v2::Shape::ROUND,
                        .flavor = v2::Flavor::CHOCOLATE,
                    },
                },
            },
        },
        Packet {
            .payload = v2::Message {
                .msg = v2::NewOrderResponse {
                    .order_id = 42,
                },
            },
        }
    );
}

TEST_CASE("bakery_cupcake_order_v2") {
    test(
        Packet {
            .payload = v2::Message {
                .msg = v2::NewOrderRequest {
                    .name = {0, 1, 2, 3, 4},
                    .order = v2::CupcakeOrder {
                        .quantity = 0x900,
                        .flavor = v2::Flavor::CHOCOLATE,
                        .frosting_flavor = v2::Flavor::CHOCOLATE,
                    },
                },
            },
        },
        Packet {
            .payload = v2::Message {
                .msg = v2::NewOrderResponse {
                    .order_id = 0x00003f3f00000900,
                },
            },
        }
    );
}

TEST_CASE("bakery_cake_order_v3") {
    test(
        Packet {
            .payload = v3::Message {
                .msg = v3::NewOrderRequest {
                    .name = {0, 1, 2, 3, 4},
                    .order = v3::CakeOrder {
                        .layers = 900,
                        .shape = v3::Shape::ROUND,
                        .flavor = v3::Flavor::CARMEL,
                    },
                },
            },
        },
        Packet {
            .payload = v3::Message {
                .msg = v3::NewOrderResponse {
                    .order_id = 42,
                },
            },
        }
    );
}

TEST_CASE("bakery_cupcake_order_v3") {
    test(
        Packet {
            .payload = v3::Message {
                .msg = v3::NewOrderRequest {
                    .name = {0, 1, 2, 3, 4},
                    .order = v3::CupcakeOrder {
                        .quantity = 0x900,
                        .flavor = v3::Flavor::CARMEL,
                        .frosting_flavor = v3::Flavor::CARMEL,
                    },
                },
            },
        },
        Packet {
            .payload = v3::Message {
                .msg = v3::NewOrderResponse {
                    .order_id = 0x00005e5e00000900,
                },
            },
        }
    );
}

TEST_CASE("bakery_cake_order_v4") {
    test(
        Packet {
            .payload = v4::Message {
                .msg = v4::NewOrderRequest {
                    .name = {0, 1, 2, 3, 4},
                    .order = v4::CakeOrder {
                        .layers = 900,
                        .shape = v4::Shape::ROUND,
                        .flavor = v4::Flavor::CARMEL,
                    },
                },
            },
        },
        Packet {
            .payload = v4::Message {
                .msg = v4::NewOrderResponse {
                    .order_id = 42,
                },
            },
        }
    );
}

TEST_CASE("bakery_cupcake_order_v4") {
    test(
        Packet {
            .payload = v4::Message {
                .msg = v4::NewOrderRequest {
                    .name = {0, 1, 2, 3, 4},
                    .order = v4::CupcakeOrder {
                        .quantity = 0x900,
                        .flavor = v4::Flavor::CARMEL,
                        .frosting_flavor = v4::Flavor::CARMEL,
                    },
                },
            },
        },
        Packet {
            .payload = v4::Message {
                .msg = v4::NewOrderResponse {
                    .order_id = 0x00005e5e00000900,
                },
            },
        }
    );
}

TEST_CASE("bakery_cancel_v4") {
    test(
        Packet {
            .payload = v4::Message {
                .msg = v4::CancelOrderRequest {
                    .order_id = 0,
                },
            },
        },
        Packet {
            .payload = v4::Message {
                .msg = v4::CancelOrderResponse {},
            },
        }
    );
}

