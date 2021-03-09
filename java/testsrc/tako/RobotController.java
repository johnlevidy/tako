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
import tako.ParseException;
import tako.Vec2;
import tako.Robot;
import takogen.test_types.RobotCmd.MsgView;
import takogen.test_types.RobotCmd.CmdVariantView;
import takogen.test_types.RobotCmd.BaseCmdView;
import takogen.test_types.RobotCmd.BaseCmdVariantView;
import takogen.test_types.RobotCmd.CmdSeqView;
import takogen.test_types.RobotCmd.RotateCmdView;
import takogen.test_types.RobotCmd.MoveCmdView;
import takogen.test_types.RobotCmd.Direction;
import takogen.test_types.RobotCmd.RotateDirection;

public class RobotController implements CmdVariantView.VoidVisitor, BaseCmdVariantView.VoidVisitor {
    private final MsgView msgView = new MsgView();

    private Robot robot;
    public RobotController(Robot robot) {
        this.robot = robot;
    }
    public void visit(MoveCmdView cmd) {
        robot.move(cmd.direction(), cmd.distance());
    }
    public void visit(RotateCmdView cmd) {
        robot.rotate(cmd.direction());
    }
    public void visit(BaseCmdView cmd) {
        cmd.cmd().accept(this);
    }
    public void visit(CmdSeqView cmd) {
        for (int i = 0; i < cmd.length(); i++) {
            cmd.cmds().get(i).cmd().accept(this);
        }
    }

    public void controlRobot(ByteBuffer buf, int offset) throws ParseException {
        msgView.parse(buf, offset);
        msgView.cmd().accept(this);
    }
}

