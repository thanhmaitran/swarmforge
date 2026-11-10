#pragma once

#include <vector>

#include "swarmforge/motion/motion_model.hpp"

namespace swarmforge {

struct Control {
    double linear{};
    double angular{};
};

/// Poses after each control step; element 0 is the start pose.
std::vector<Pose2D> integrate_trajectory(const MotionModel& model, const Pose2D& start,
                                         const std::vector<Control>& controls, double dt);

}  // namespace swarmforge
