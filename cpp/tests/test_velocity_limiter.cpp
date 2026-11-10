#include "check.hpp"
#include "swarmforge/motion/velocity_limiter.hpp"

using namespace swarmforge;

TEST(speed_is_clamped) {
    VelocityLimiter lim(1.0, 100.0, 2.0, 100.0);
    double l = 0, a = 0;
    lim.limit(0, 0, 5.0, -9.0, 0.1, l, a);
    CHECK_NEAR(l, 1.0, 1e-12);
    CHECK_NEAR(a, -2.0, 1e-12);
}

TEST(acceleration_is_limited) {
    VelocityLimiter lim(2.0, 0.5, 2.0, 1.0);
    double l = 0, a = 0;
    lim.limit(0, 0, 2.0, 2.0, 0.1, l, a);
    CHECK_NEAR(l, 0.05, 1e-12);
    CHECK_NEAR(a, 0.1, 1e-12);
}

TEST(invalid_limits_rejected) {
    CHECK_THROWS(VelocityLimiter(0.0, 1, 1, 1));
    CHECK_THROWS(VelocityLimiter(1, -1, 1, 1));
}

SF_TEST_MAIN()
