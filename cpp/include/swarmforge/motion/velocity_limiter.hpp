#pragma once

namespace swarmforge {

/// Clamps commanded velocities and limits per-step acceleration.
class VelocityLimiter {
public:
    /// @throws std::invalid_argument if any limit is not strictly positive.
    VelocityLimiter(double max_speed, double max_accel, double max_angular, double max_angular_accel);

    void limit(double current_linear, double current_angular, double desired_linear,
               double desired_angular, double dt, double& out_linear, double& out_angular) const;

private:
    double max_speed_, max_accel_, max_angular_, max_angular_accel_;
};

}  // namespace swarmforge
