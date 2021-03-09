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
import java.lang.Long;
import static takogen.test_types.LargeIntConstant.*;

public class TestLargeIntConstant {
    @Test
    public void largeIntConstant() {
        Assertions.assertEquals(C_I8_MIN, -128);
        Assertions.assertEquals(C_I8_MAX, 127);
        Assertions.assertEquals(C_LI16_MIN, -32768);
        Assertions.assertEquals(C_LI16_MAX, 32767);
        Assertions.assertEquals(C_LI32_MIN, -2147483648);
        Assertions.assertEquals(C_LI32_MAX, 2147483647);
        Assertions.assertEquals(C_LI64_MIN, -9223372036854775808L);
        Assertions.assertEquals(C_LI64_MAX, 9223372036854775807L);
        Assertions.assertEquals(C_BI16_MIN, -32768);
        Assertions.assertEquals(C_BI16_MAX, 32767);
        Assertions.assertEquals(C_BI32_MIN, -2147483648);
        Assertions.assertEquals(C_BI32_MAX, 2147483647);
        Assertions.assertEquals(C_BI64_MIN, -9223372036854775808L);
        Assertions.assertEquals(C_BI64_MAX, 9223372036854775807L);
        Assertions.assertEquals(C_U8_MIN, 0);
        Assertions.assertEquals(C_U8_MAX, (byte) 255);
        Assertions.assertEquals(C_LU16_MIN, 0);
        Assertions.assertEquals(C_LU16_MAX, (short) 65535);
        Assertions.assertEquals(C_LU32_MIN, 0);
        Assertions.assertEquals(C_LU32_MAX, (int) 4294967295L);
        Assertions.assertEquals(C_LU64_MIN, 0);
        Assertions.assertEquals(C_LU64_MAX, Long.parseUnsignedLong("18446744073709551615"));
        Assertions.assertEquals(C_BU16_MIN, 0);
        Assertions.assertEquals(C_BU16_MAX, (short) 65535);
        Assertions.assertEquals(C_BU32_MIN, 0);
        Assertions.assertEquals(C_BU32_MAX, (int) 4294967295L);
        Assertions.assertEquals(C_BU64_MIN, 0);
        Assertions.assertEquals(C_BU64_MAX, Long.parseUnsignedLong("18446744073709551615"));
    }
}

