#include "swarmforge/motion/trajectory.hpp"

namespace swarmforge {

std::vector<Pose2D> integrate_trajectory(const MotionModel& model, const Pose2D& start,
                                         const std::vector<Control>& controls, double dt) {
    std::vector<Pose2D> poses;
    poses.reserve(controls.size() + 1);
    poses.push_back(start);
    for (const auto& c : controls) poses.push_back(model.update(poses.back(), c.linear, c.angular, dt));
    return poses;
}

}  // namespace swarmforge
