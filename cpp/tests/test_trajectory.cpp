#include "check.hpp"
#include "swarmforge/motion/differential_drive.hpp"
#include "swarmforge/motion/trajectory.hpp"

using namespace swarmforge;

TEST(trajectory_has_n_plus_one_poses) {
    DifferentialDrive d(0.05, 0.30);
    auto poses = integrate_trajectory(d, {0, 0, 0}, std::vector<Control>(5, {1.0, 0.0}), 0.1);
    CHECK(poses.size() == 6);
    CHECK_NEAR(poses.back().x, 0.5, 1e-12);
}

TEST(empty_controls_return_start) {
    DifferentialDrive d(0.05, 0.30);
    auto poses = integrate_trajectory(d, {1, 2, 3}, {}, 0.1);
    CHECK(poses.size() == 1);
}

SF_TEST_MAIN()
