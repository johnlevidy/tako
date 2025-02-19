#include <cassert>
#include <gsl.hpp>
#include <iomanip>
#include <iostream>
#include <core.hh>
#include <cstddef>
#include <optional>
#include <vector>
#include "tako/tako.hh"
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
    .three = 6,
    .four = test_types::milestone1::InnerVariant {
      .inner = test_types::milestone1::MiniIntegerType {
        .contained = 4
      }
    },
    .five = 123
  };
  // Expected sizing
  // one = 4
  // two = 1 ( tag ) + 4
  // three = 4
  // 13 total
  std::vector<gsl::byte> request_bytes = request.serialize();

  test_types::milestone1::PacketView view = test_types::milestone1::PacketView::render(request_bytes);
  // parsed.
  tako::ParseInfo<std::optional<test_types::milestone1::PacketPeek>> peek = test_types::milestone1::PacketPeek::peek(request_bytes);

  std::cout << "Now trying a corrupt request\n";
  auto corrupt_request = test_types::milestone1::Packet {
    .one = 5, // 4
    .two = test_types::milestone1::BigIntegerType {
      .contained = 3,
    }, // 5 ( 4 + 1b tag )
    .three = 6, // 4
    .four = test_types::milestone1::InnerVariant {
      .inner = test_types::milestone1::MiniIntegerType {
        .contained = 4
      }
    }, // 6 ( 4 + 1b tag + 1b tag )
    .five = 123 // 4
  };
  std::vector<gsl::byte> corrupt_request_bytes = request.serialize();
  assert(int(corrupt_request_bytes[4]) == 1);
  // Bad tag on the wire!! I changed the mini integer type tag, I think.
  // It still seems to think I can go to 19 though, so something is wrong ( TODO )
  // I think it's not bubbling up the value from underneath or something.
  // Actually ( leaving above for posterity ) it appears to be less wrong than initially thought
  // the innermost type whose bytes i changed does see its buffer trimmed / the sentinel
  // is reflected. the outer one just needs to bubble up the failure to definitively parse a length
  corrupt_request_bytes[14] = gsl::byte{0x13};
  tako::ParseInfo<std::optional<test_types::milestone1::PacketPeek>> corrupt_peek = test_types::milestone1::PacketPeek::peek(corrupt_request_bytes);
  auto b = corrupt_peek.rendered->backing_buffer();
  // 23 bytes look good this time, is that right??
  std::cout << (b.end() - b.begin()) << "\n";
  std::cout << "Successfully ran test\n";
}
