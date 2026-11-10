#include "swarmforge/geometry/geometry_utils.hpp"

#include <cmath>

#include "swarmforge/common/types.hpp"

namespace swarmforge {

double normalize_angle(double theta) {
    double t = std::fmod(theta + kPi, kTwoPi);
    if (t <= 0.0) t += kTwoPi;
    return t - kPi;
}

double distance(const Pose2D& a, const Pose2D& b) { return std::hypot(a.x - b.x, a.y - b.y); }

}  // namespace swarmforge
