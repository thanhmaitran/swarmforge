#include "swarmforge/motion/differential_drive.hpp"

#include <cmath>
#include <stdexcept>

#include "swarmforge/geometry/geometry_utils.hpp"

namespace swarmforge {

DifferentialDrive::DifferentialDrive(double wheel_radius, double wheel_base)
    : wheel_radius_(wheel_radius), wheel_base_(wheel_base) {
    if (!(wheel_radius > 0.0) || !std::isfinite(wheel_radius) || !(wheel_base > 0.0) ||
        !std::isfinite(wheel_base)) {
        throw std::invalid_argument("wheel_radius and wheel_base must be positive and finite");
    }
}

Pose2D DifferentialDrive::update(const Pose2D& pose, double v, double w, double dt) const {
    if (!(dt >= 0.0) || !std::isfinite(dt)) throw std::invalid_argument("dt must be finite and >= 0");
    if (!std::isfinite(v) || !std::isfinite(w) || !std::isfinite(pose.x) || !std::isfinite(pose.y) ||
        !std::isfinite(pose.theta)) {
        throw std::invalid_argument("non-finite input");
    }
    return {pose.x + v * std::cos(pose.theta) * dt, pose.y + v * std::sin(pose.theta) * dt,
            normalize_angle(pose.theta + w * dt)};
}

void DifferentialDrive::body_velocity(double wl, double wr, double& linear, double& angular) const {
    linear = wheel_radius_ / 2.0 * (wr + wl);
    angular = wheel_radius_ / wheel_base_ * (wr - wl);
}

}  // namespace swarmforge
