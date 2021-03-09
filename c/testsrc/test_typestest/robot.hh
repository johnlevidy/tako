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

#pragma once

#include "test_types/robot_cmd.hh"

namespace test_types {

struct Attitude {
    int dx, dy;
    bool operator ==(const Attitude &b) const { return dx == b.dx && dy == b.dy; }
};

class Robot {
public:
    using Direction = robot_cmd::Direction;
    using RotateDirection = robot_cmd::RotateDirection;

    // Initializes a new robot at (0, 0) facing in the in positive y direction
    Robot() : x_(0), y_(0), dx_(0), dy_(1) {}

    int x() { return x_; };
    int y() { return y_; };

    Attitude attitude() { return Attitude{ dx_, dy_ }; };

    void move(Direction dir, int s) {
        if (dir == Direction::BACKWARDS) {
            s *= -1;
        }
        x_ += dx_ * s;
        y_ += dy_ * s;
    }

    void rotate(RotateDirection dir) {
        if (dir == RotateDirection::LEFT_90) {
            if (dx_ == 0 && dy_ == 1) {
                dx_ = -1;
                dy_ = 0;
            } else if (dx_ == -1 && dy_ == 0) {
                dx_ = 0;
                dy_ = -1;
            } else if (dx_ == 0 && dy_ == -1) {
                dx_ = 1;
                dy_ = 0;
            } else if (dx_ == 1 && dy_ == 0) {
                dx_ = 0;
                dy_ = 1;
            }
        } else {
            if (dx_ == 0 && dy_ == 1) {
                dx_ = 1;
                dy_ = 0;
            } else if (dx_ == 1 && dy_ == 0) {
                dx_ = 0;
                dy_ = -1;
            } else if (dx_ == 0 && dy_ == -1) {
                dx_ = -1;
                dy_ = 0;
            } else if (dx_ == -1 && dy_ == 0) {
                dx_ = 0;
                dy_ = 1;
            }
        }
    }
private:
    int x_, y_;
    // Direction of the robot, represented as a unit vector
    int dx_, dy_;
};

class RobotManager {
private:
    Robot& robot_;

public:
    RobotManager(Robot& robot) : robot_{robot} {}

    void operator()(const robot_cmd::MoveCmdView& cmd) const {
        robot_.move(cmd.direction(), cmd.distance());
    }

    void operator()(const robot_cmd::RotateCmdView& cmd) const {
        robot_.rotate(cmd.direction());
    }

    void operator()(const robot_cmd::BaseCmdView& cmd) const {
        cmd.cmd().accept(*this);
    }

    void operator()(const robot_cmd::CmdSeqView& cmd) const {
        for (int i = 0; i < cmd.length(); i++) {
            cmd.cmds()[i].cmd().accept(*this);
        }
    }
};

bool control_robot(gsl::span<const gsl::byte> buf, Robot& robot) {
    auto result = robot_cmd::MsgView::parse(buf);
    if (!result) { return false; }
    auto msg = result->rendered;

    RobotManager manager{robot};
    msg.cmd().accept(manager);
    return true;
}

};
