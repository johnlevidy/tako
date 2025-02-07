#include <gsl.hpp>
#include <iostream>
#include <core.hh>
#include <cstddef>
#include <vector>

int main() {
  // Build a Milestone1
  auto request = test_types::milestone1::Packet {
    .one = 5,
    .two = test_types::milestone1::BigIntegerType {
      .contained = 3,
    },
    .three = 6
  };
  std::vector<gsl::byte> request_bytes = request.serialize();
  std::cout << "Hello\n";

  test_types::milestone1::PacketView view = test_types::milestone1::PacketView::render(request_bytes);
  std::cout << view.one() << "\n";
  std::cout << view.three() << "\n";
  // parsed.
}
