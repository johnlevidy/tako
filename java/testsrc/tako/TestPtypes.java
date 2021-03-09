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

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import tako.ParseException;
import static tako.PtypesRuntime.*;
import takogen.tako.Ptypes;
import takogen.test_types.PtypesTestTypes;
import static tako.Helpers.*;

public class TestPtypes {
    @Test
    public void ptypeString() {
        var start = "hello world";
        var x = makePtypeStringL16(start);
        Assertions.assertEquals(start, makeString(x));
    }

    @Test
    public void maybeNum() throws ParseException {
        var someNum = new PtypesTestTypes.Optional();
        someNum.maybeNum().set(Ptypes.Lu32.class).setValue(42);
        var noneNum = new PtypesTestTypes.Optional();
        noneNum.maybeNum().set(Ptypes.Empty.class);

        someNum.maybeNum().accept(new PtypesTestTypes.MaybeNum.VoidVisitor() {
            public void visit(Ptypes.Lu32 x) {
                Assertions.assertEquals(x.value(), 42);
            }
            public void visit(Ptypes.Empty x) {
                Assertions.fail("Should not be empty");
            }
        });
        noneNum.maybeNum().accept(new PtypesTestTypes.MaybeNum.VoidVisitor() {
            public void visit(Ptypes.Lu32 x) {
                Assertions.fail("Should not be an Lu32");
            }
            public void visit(Ptypes.Empty x) {}
        });

        var someNumView = new PtypesTestTypes.OptionalView();
        someNumView.parse(someNum.serialize(), 0);
        var noneNumView = new PtypesTestTypes.OptionalView();
        noneNumView.parse(noneNum.serialize(), 0);

        someNumView.maybeNum().accept(new PtypesTestTypes.MaybeNumView.VoidVisitor() {
            public void visit(Ptypes.Lu32View x) {
                Assertions.assertEquals(x.value(), 42);
            }
            public void visit(Ptypes.EmptyView x) {
                Assertions.fail("Should not be empty");
            }
        });
        noneNumView.maybeNum().accept(new PtypesTestTypes.MaybeNumView.VoidVisitor() {
            public void visit(Ptypes.Lu32View x) {
                Assertions.fail("Should not be an Lu32");
            }
            public void visit(Ptypes.EmptyView x) {}
        });
    }
}
