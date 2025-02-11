#include <cassert>
#include <gsl.hpp>
#include <iomanip>
#include <iostream>
#include <core_modified.hh>
#include <cstddef>
#include <vector>
#include "tl/expected.hpp"

template<typename T>
void maybe_print(std::optional<T> t) {
  if (t) {
    std::cout << t.value() << "\n";
    return;
  }
  std::cout << "No value\n";
}

int main() {
  // Build a Milestone1
  auto request = test_types::milestone1::Packet {
    .one = 5,
    .two = test_types::milestone1::BigIntegerType {
      .contained = 3,
    },
    .three = 6
  };
  // Expected sizing
  // one = 4
  // two = 1 ( tag ) + 4
  // three = 4
  // 13 total
  std::vector<gsl::byte> request_bytes = request.serialize();

  test_types::milestone1::PacketView view = test_types::milestone1::PacketView::render(request_bytes);
  // parsed.
  test_types::milestone1::PacketPeek peek = test_types::milestone1::PacketView::peek(request_bytes);
  assert(13 == peek.good_bytes);

  auto corrupt_request = test_types::milestone1::Packet {
    .one = 5,
    .two = test_types::milestone1::BigIntegerType {
      .contained = 3,
    },
    .three = 6
  };
  std::vector<gsl::byte> corrupt_request_bytes = request.serialize();
  assert(int(corrupt_request_bytes[4]) == 1);
  // Bad tag on the wire!!
  corrupt_request_bytes[4] = gsl::byte{0x03};
  test_types::milestone1::PacketPeek corrupt_peek = test_types::milestone1::PacketView::peek(corrupt_request_bytes);
  assert(4 == corrupt_peek.good_bytes);
  assert(5 == corrupt_peek.one().value());
  assert(std::nullopt == corrupt_peek.two());
  assert(std::nullopt == corrupt_peek.three());
  std::cout << "Successfully ran test\n";
}
