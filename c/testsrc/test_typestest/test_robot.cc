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

#include "catch2/catch.hpp"
#include "robot.hh"

using test_types::Robot;
using test_types::Attitude;
using namespace test_types;
using namespace std;

TEST_CASE("robot") {
    Robot r;
    CHECK(r.x() == 0);
    CHECK(r.y() == 0);
    CHECK(r.attitude() == Attitude{0, 1});

    {
        robot_cmd::Msg m {
            .cmd = {
                robot_cmd::MoveCmd {.direction = robot_cmd::Direction::FORWARDS, .distance = 1},
            },
        };
        auto built = m.serialize();
        CHECK(control_robot(built, r));
        CHECK(r.x() == 0);
        CHECK(r.y() == 1);
        CHECK(r.attitude() == Attitude{0, 1});
    }
    {
        robot_cmd::Msg m {
            .cmd = {
                robot_cmd::CmdSeq {
                    .cmds = {
                        {robot_cmd::RotateCmd {robot_cmd::RotateDirection::LEFT_90}},
                        {robot_cmd::MoveCmd {robot_cmd::Direction::FORWARDS, .distance = 1}},
                    },
                },
            },
        };
        auto built = m.serialize();
        CHECK(control_robot(built, r));
        CHECK(r.x() == -1);
        CHECK(r.y() == 1);
        CHECK(r.attitude() == Attitude{-1, 0});
    }
}

