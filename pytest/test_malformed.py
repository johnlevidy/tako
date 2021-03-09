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

import io
from tako.main import main


class TestMalformed(TestCase):
    def check_errors(self, proto: str) -> None:
        output = io.StringIO()
        status = main(["generate", "takolsir/", proto, "lsir"], output)
        self.assertNotEqual(status, 0)

    def test_not_a_protocol(self) -> None:
        self.check_errors("test_types.malformed.NotAProtocol")

    def test_bad_struct_name(self) -> None:
        self.check_errors("test_types.malformed.BadStructName")

    def test_bad_field_name(self) -> None:
        self.check_errors("test_types.malformed.BadFieldName")

    def test_restricted_field_name(self) -> None:
        self.check_errors("test_types.malformed.RestrictedFieldName")

    def test_bad_suffix(self) -> None:
        self.check_errors("test_types.malformed.BadSuffix")

    def test_multiple_protocol_definition(self) -> None:
        self.check_errors("test_types.malformed.MultipleProtocolDefinition")
