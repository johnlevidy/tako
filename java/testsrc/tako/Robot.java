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

import tako.Vec2;
import takogen.test_types.RobotCmd.Direction;
import takogen.test_types.RobotCmd.RotateDirection;

public class Robot {
    private Vec2 loc;
    private Vec2 attitude;

    public Robot() {
        this.loc = new Vec2(0, 0);
        this.attitude = new Vec2(0, 1);
    }

    public Vec2 loc() {
        return loc;
    }
    public Vec2 attitude() {
        return attitude;
    }

    public void move(Direction dir, int s) {
        if (dir.equals(Direction.BACKWARDS)) {
            s *= -1;
        }
        loc.mac(attitude, s);
    }

    public void rotate(RotateDirection dir) {
        if (dir.equals(RotateDirection.LEFT_90)) {
            if (attitude.x() == 0 && attitude.y() == 1) {
                attitude.setX(-1);
                attitude.setY(0);
            } else if (attitude.x() == -1 && attitude.y() == 0) {
                attitude.setX(0);
                attitude.setY(-1);
            } else if (attitude.x() == 0 && attitude.y() == -1) {
                attitude.setX(1);
                attitude.setY(0);
            } else if (attitude.x() == 1 && attitude.y() == 0) {
                attitude.setX(0);
                attitude.setY(1);
            }
        } else {
            if (attitude.x() == 0 && attitude.y() == 1) {
                attitude.setX(1);
                attitude.setY(0);
            } else if (attitude.x() == 1 && attitude.y() == 0) {
                attitude.setX(0);
                attitude.setY(-1);
            } else if (attitude.x() == 0 && attitude.y() == -1) {
                attitude.setX(-1);
                attitude.setY(0);
            } else if (attitude.x() == -1 && attitude.y() == 0) {
                attitude.setX(0);
                attitude.setY(1);
            }
        }
    }
}
