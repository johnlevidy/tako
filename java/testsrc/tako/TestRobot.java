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
import tako.Robot;
import tako.RobotController;
import takogen.test_types.RobotCmd.Msg;
import takogen.test_types.RobotCmd.CmdVariant;
import takogen.test_types.RobotCmd.BaseCmd;
import takogen.test_types.RobotCmd.BaseCmdVariant;
import takogen.test_types.RobotCmd.CmdSeq;
import takogen.test_types.RobotCmd.RotateCmd;
import takogen.test_types.RobotCmd.MoveCmd;
import takogen.test_types.RobotCmd.Direction;
import takogen.test_types.RobotCmd.RotateDirection;

public class TestRobot {
    @Test
    public void robot() throws ParseException {
        Robot r = new Robot();
        RobotController c = new RobotController(r);
        Assertions.assertEquals(r.loc().x(), 0);
        Assertions.assertEquals(r.loc().y(), 0);
        Assertions.assertEquals(r.attitude().x(), 0);
        Assertions.assertEquals(r.attitude().y(), 1);

        Msg msg = new Msg().init()
            .cmd().enter()
                .set(MoveCmd.marker).enter()
                    .direction(Direction.FORWARDS)
                    .distance(1)
                    .finish()
                .finish()
            .finish();
        c.controlRobot(msg.serialize(), 0);
        Assertions.assertEquals(r.loc().x(), 0);
        Assertions.assertEquals(r.loc().y(), 1);
        Assertions.assertEquals(r.attitude().x(), 0);
        Assertions.assertEquals(r.attitude().y(), 1);

        msg.init()
            .cmd().enter()
                .set(CmdSeq.marker).enter()
                    .cmds((x) -> {
                        x.clear();
                        x.add(new BaseCmd().init()
                            .cmd().enter()
                                .set(RotateCmd.marker).enter()
                                    .direction(RotateDirection.LEFT_90)
                                    .finish()
                                .finish()
                            .finish()
                        );
                        x.add(new BaseCmd().init()
                            .cmd().enter()
                                .set(MoveCmd.marker).enter()
                                    .direction(Direction.FORWARDS)
                                    .distance(1)
                                    .finish()
                                .finish()
                            .finish()
                        );
                        return x;
                    })
                .finish()
            .finish();
        c.controlRobot(msg.serialize(), 0);
        Assertions.assertEquals(r.loc().x(), -1);
        Assertions.assertEquals(r.loc().y(), 1);
        Assertions.assertEquals(r.attitude().x(), -1);
        Assertions.assertEquals(r.attitude().y(), 0);
    }
}
