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

import java.util.ArrayList;
import takogen.tako.Ptypes;
import tako.FixedSizeTakoType;
import it.unimi.dsi.fastutil.bytes.ByteArrayList;

public class PtypesRuntime {

    public static Ptypes.StringL8 makePtypeStringL8(String str) {
        return new Ptypes.StringL8().init()
            .data((x) -> ByteArrayList.wrap(str.getBytes()))
            .finish();
    }
    public static Ptypes.StringL16 makePtypeStringL16(String str) {
        return new Ptypes.StringL16().init()
            .data((x) -> ByteArrayList.wrap(str.getBytes()))
            .finish();
    }
    public static Ptypes.StringL32 makePtypeStringL32(String str) {
        return new Ptypes.StringL32().init()
            .data((x) -> ByteArrayList.wrap(str.getBytes()))
            .finish();
    }

    public static String makeString(Ptypes.StringL8 str) {
        return new String(str.data().elements());
    }
    public static String makeString(Ptypes.StringL16 str) {
        return new String(str.data().elements());
    }
    public static String makeString(Ptypes.StringL32 str) {
        return new String(str.data().elements());
    }
}
