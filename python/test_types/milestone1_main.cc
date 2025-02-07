#include <gsl.hpp>
#include "core.hh"
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

}
