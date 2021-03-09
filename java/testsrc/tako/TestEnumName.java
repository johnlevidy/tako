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

package tako;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import takogen.test_types.EnumName.Dolphins;

public class TestEnumName {
    @Test
    public void enumName() {
        Assertions.assertEquals(Dolphins.COMMON.name(), "COMMON");
        Assertions.assertEquals(Dolphins.BOTTLENOSE.name(), "BOTTLENOSE");
        Assertions.assertEquals(Dolphins.SPINNER.name(), "SPINNER");
        Assertions.assertEquals(Dolphins.PACIFIC_WHITE_SIDED.name(), "PACIFIC_WHITE_SIDED");
        Assertions.assertEquals(Dolphins.PILOT_WHALE.name(), "PILOT_WHALE");
    }
}
