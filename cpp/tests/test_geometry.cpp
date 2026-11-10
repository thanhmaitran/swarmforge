#include "check.hpp"
#include "swarmforge/common/types.hpp"
#include "swarmforge/geometry/geometry_utils.hpp"

using namespace swarmforge;

TEST(normalize_angle_wraps_into_half_open_interval) {
    CHECK_NEAR(normalize_angle(0.0), 0.0, 1e-12);
    CHECK_NEAR(normalize_angle(kTwoPi), 0.0, 1e-12);
    CHECK_NEAR(normalize_angle(kPi), kPi, 1e-12);
    CHECK_NEAR(normalize_angle(-kPi), kPi, 1e-12);
    CHECK_NEAR(normalize_angle(3.0 * kPi), kPi, 1e-12);
    CHECK_NEAR(normalize_angle(-0.5 - 4.0 * kTwoPi), -0.5, 1e-9);
}

TEST(distance_between_poses) {
    CHECK_NEAR(distance({0, 0, 0}, {3, 4, 1}), 5.0, 1e-12);
}

TEST(vector_operations) {
    Vector2 a{1, 2}, b{3, -1};
    CHECK_NEAR((a + b).x, 4.0, 1e-12);
    CHECK_NEAR(a.dot(b), 1.0, 1e-12);
    CHECK_NEAR(a.cross(b), -7.0, 1e-12);
    Vector2 c{3, 4};
    CHECK_NEAR(c.norm(), 5.0, 1e-12);
}

SF_TEST_MAIN()
