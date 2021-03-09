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
import takogen.test_types.Basic.ThingMsgView;
import takogen.test_types.EnumRange.Enum02MsgView;
import takogen.test_types.EnumRange.Enum02;
import static tako.Helpers.*;

public class TestParseErrors {
    @Test
    public void thingMsg() {
        ByteBuffer variantToShort = bytes(
            // thing_type (Thing.tag_type(u8))
            0x00
            // thing
            // NOTE IT IS NOT ACTUALLY THERE
        );
        ByteBuffer stringToShort = bytes(
            // thing_type (Thing.tag_type(u8))
            0x00,
            // thing
            // name (External.String)
            // len (li32)
            0x03, 0x00, 0x00, 0x00,
            // data (Seq(i8, this.len))
            // NOTE THERE IS NOT ENOUGH DATA
            // Only 2 chars
            98, 111
        );
        ByteBuffer malformed = bytes(
            // thing_type (Thing.tag_type(u8))
            // NOTE NOT A VALID THING TYPE
            0xFF
        );

        Assertions.assertThrows(ParseException.NotEnoughData.class, () -> {
            ThingMsgView parsed = new ThingMsgView();
            parsed.parse(variantToShort, 0);
        });
        Assertions.assertThrows(ParseException.NotEnoughData.class, () -> {
            ThingMsgView parsed = new ThingMsgView();
            parsed.parse(stringToShort, 0);
        });
        Assertions.assertThrows(ParseException.Malformed.class, () -> {
            ThingMsgView parsed = new ThingMsgView();
            parsed.parse(malformed, 0);
        });
    }

    @Test
    public void errorsEnum() throws ParseException {
        ByteBuffer thingff = bytes(0xff);
        ByteBuffer thing00 = bytes(0x00);
        ByteBuffer thing01 = bytes(0x01);
        ByteBuffer thing02 = bytes(0x02);
        ByteBuffer thing03 = bytes(0x03);

        Enum02MsgView parsed = new Enum02MsgView();
        Assertions.assertThrows(ParseException.Malformed.class, () -> {
            parsed.parse(thingff, 0);
        });
        parsed.parse(thing00, 0);
        Assertions.assertEquals(parsed.thing(), Enum02.THING0);
        parsed.parse(thing01, 0);
        Assertions.assertEquals(parsed.thing(), Enum02.THING1);
        parsed.parse(thing02, 0);
        Assertions.assertEquals(parsed.thing(), Enum02.THING2);
        Assertions.assertThrows(ParseException.Malformed.class, () -> {
            parsed.parse(thing03, 0);
        });

        parsed.render(thingff, 0);
        Assertions.assertEquals(parsed.thing(), Enum02.makeUnsafe((byte) 0xff));
        parsed.render(thing03, 0);
        Assertions.assertEquals(parsed.thing(), Enum02.makeUnsafe((byte) 0x03));
    }
}

