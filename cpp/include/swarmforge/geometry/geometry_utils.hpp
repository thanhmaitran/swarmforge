#pragma once

#include "swarmforge/geometry/pose2d.hpp"
#include "swarmforge/geometry/vector2.hpp"

namespace swarmforge {

/// Wrap an angle to the interval (-pi, pi].
double normalize_angle(double theta);

/// Euclidean distance between the positions of two poses.
double distance(const Pose2D& a, const Pose2D& b);

}  // namespace swarmforge
