#pragma once

#include "swarmforge/motion/motion_model.hpp"

namespace swarmforge {

/// Differential-drive robot, forward-Euler integration.
///   x += v cos(theta) dt,  y += v sin(theta) dt,  theta += omega dt
class DifferentialDrive final : public MotionModel {
public:
    /// @throws std::invalid_argument if a dimension is not strictly positive/finite.
    DifferentialDrive(double wheel_radius, double wheel_base);

    /// @throws std::invalid_argument if dt is negative or an input is not finite.
    Pose2D update(const Pose2D& pose, double linear_velocity, double angular_velocity,
                  double dt) const override;

    /// v = r/2 (wR + wL), omega = r/L (wR - wL)
    void body_velocity(double omega_left, double omega_right, double& linear, double& angular) const;

    double wheel_radius() const { return wheel_radius_; }
    double wheel_base() const { return wheel_base_; }

private:
    double wheel_radius_;
    double wheel_base_;
};

}  // namespace swarmforge
