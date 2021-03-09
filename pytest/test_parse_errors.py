# Copyright 2020 Jacob Glueck
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest import TestCase

from takogen.test_types import Basic
from tako.runtime import ParseError


class TestParseErrors(TestCase):
    def test_parse_errors_person(self) -> None:
        # fmt: off
        variant_to_short = bytes([
            # thing_type (Thing.tag_type(u8))
            0x00,
            # thing
            # NOTE IT IS NOT ACTUALLY THERE
        ])
        string_to_short = bytes([
            # thing_type (Thing.tag_type(u8))
            0x00,
            # thing
            # name (External.String)
            # len (li32)
            0x03, 0x00, 0x00, 0x00,
            # data (Seq(i8, this.len))
            # NOTE THERE IS NOT ENOUGH DATA
            # Only 2 chars
            98, 111,
        ])
        malformed = bytes([
            # thing_type (Thing.tag_type(u8))
            # NOTE NOT A VALID THING TYPE
            0xFF,
        ])
        # fmt: on
        self.assertEqual(
            Basic.ThingMsg.parse(variant_to_short, 0), ParseError.NOT_ENOUGH_DATA
        )
        self.assertEqual(
            Basic.ThingMsg.parse(string_to_short, 0), ParseError.NOT_ENOUGH_DATA
        )
        self.assertEqual(Basic.ThingMsg.parse(malformed, 0), ParseError.MALFORMED)
