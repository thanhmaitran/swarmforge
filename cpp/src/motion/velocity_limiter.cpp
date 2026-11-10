#include "swarmforge/motion/velocity_limiter.hpp"

#include <algorithm>
#include <stdexcept>

namespace swarmforge {

namespace {
double clamp(double v, double lim) { return std::max(-lim, std::min(lim, v)); }
}  // namespace

VelocityLimiter::VelocityLimiter(double max_speed, double max_accel, double max_angular,
                                 double max_angular_accel)
    : max_speed_(max_speed),
      max_accel_(max_accel),
      max_angular_(max_angular),
      max_angular_accel_(max_angular_accel) {
    if (!(max_speed > 0.0) || !(max_accel > 0.0) || !(max_angular > 0.0) || !(max_angular_accel > 0.0)) {
        throw std::invalid_argument("limits must be strictly positive");
    }
}

void VelocityLimiter::limit(double cur_l, double cur_a, double des_l, double des_a, double dt,
                            double& out_l, double& out_a) const {
    if (!(dt > 0.0)) throw std::invalid_argument("dt must be positive");
    const double l = clamp(des_l, max_speed_);
    const double a = clamp(des_a, max_angular_);
    out_l = cur_l + clamp(l - cur_l, max_accel_ * dt);
    out_a = cur_a + clamp(a - cur_a, max_angular_accel_ * dt);
}

}  // namespace swarmforge
