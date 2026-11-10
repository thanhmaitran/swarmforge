#include "check.hpp"
#include "swarmforge/common/types.hpp"
#include "swarmforge/motion/differential_drive.hpp"

using namespace swarmforge;

TEST(straight_line_motion) {
    DifferentialDrive d(0.05, 0.30);
    Pose2D p{0, 0, 0};
    for (int i = 0; i < 10; ++i) p = d.update(p, 1.0, 0.0, 0.1);
    CHECK_NEAR(p.x, 1.0, 1e-12);
    CHECK_NEAR(p.y, 0.0, 1e-12);
}

TEST(pure_rotation_keeps_position) {
    DifferentialDrive d(0.05, 0.30);
    Pose2D p = d.update({1, 2, 0}, 0.0, kPi / 2, 1.0);
    CHECK_NEAR(p.x, 1.0, 1e-12);
    CHECK_NEAR(p.y, 2.0, 1e-12);
    CHECK_NEAR(p.theta, kPi / 2, 1e-12);
}

TEST(combined_motion_and_heading_wrap) {
    DifferentialDrive d(0.05, 0.30);
    Pose2D p{0, 0, 3.0};
    p = d.update(p, 0.5, 1.0, 0.5);
    CHECK(p.theta <= kPi && p.theta > -kPi);
    CHECK_NEAR(p.theta, 3.5 - kTwoPi, 1e-12);
}

TEST(zero_velocity_is_identity) {
    DifferentialDrive d(0.05, 0.30);
    Pose2D p = d.update({1, 2, 0.3}, 0.0, 0.0, 0.1);
    CHECK_NEAR(p.x, 1.0, 1e-15);
    CHECK_NEAR(p.theta, 0.3, 1e-15);
}

TEST(negative_dt_rejected) {
    DifferentialDrive d(0.05, 0.30);
    CHECK_THROWS(d.update({0, 0, 0}, 1.0, 0.0, -0.1));
}

TEST(invalid_dimensions_rejected) {
    CHECK_THROWS(DifferentialDrive(0.0, 0.3));
    CHECK_THROWS(DifferentialDrive(0.05, -1.0));
    CHECK_THROWS(DifferentialDrive(std::nan(""), 0.3));
}

TEST(wheel_speeds_to_body_velocity) {
    DifferentialDrive d(0.05, 0.30);
    double v = 0, w = 0;
    d.body_velocity(10.0, 10.0, v, w);
    CHECK_NEAR(v, 0.5, 1e-12);
    CHECK_NEAR(w, 0.0, 1e-12);
    d.body_velocity(-10.0, 10.0, v, w);
    CHECK_NEAR(v, 0.0, 1e-12);
    CHECK_NEAR(w, 0.05 / 0.30 * 20.0, 1e-12);
}

TEST(numerical_stability_long_run) {
    DifferentialDrive d(0.05, 0.30);
    Pose2D p{0, 0, 0};
    for (int i = 0; i < 1000000; ++i) p = d.update(p, 0.5, 0.2, 0.001);
    CHECK(std::isfinite(p.x) && std::isfinite(p.y));
    CHECK(p.theta <= kPi && p.theta > -kPi);
}

SF_TEST_MAIN()
