#pragma once

#include "swarmforge/geometry/pose2d.hpp"

namespace swarmforge {

class MotionModel {
public:
    virtual ~MotionModel() = default;
    virtual Pose2D update(const Pose2D& pose, double linear_velocity, double angular_velocity,
                          double dt) const = 0;
};

}  // namespace swarmforge
