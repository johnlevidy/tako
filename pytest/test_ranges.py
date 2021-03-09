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

from tako.util.ranges import Range, find_ranges


class TestRanges(TestCase):
    def test_find_ranges(self) -> None:
        self.assertEqual(
            [Range(0, 10)], find_ranges([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        )
        self.assertEqual(
            [Range(0, 4), Range(6, 10)], find_ranges([0, 1, 2, 3, 4, 6, 7, 8, 9, 10])
        )
        self.assertEqual([Range(0, 0)], find_ranges([0]))
        self.assertEqual([], find_ranges([]))
