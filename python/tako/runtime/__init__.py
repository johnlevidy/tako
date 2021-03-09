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

# This file depends on NOTHING else in tako
# This is so potentially the python runtime can be shipped without the generator
# Note the the generator can depend on the runtime

import enum

# This mirrors the ParseError enum in tako.hh
@enum.unique
class ParseError(enum.Enum):
    MALFORMED = enum.auto()
    NOT_ENOUGH_DATA = enum.auto()
