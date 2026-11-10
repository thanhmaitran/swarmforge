// Usage: bench_kinematics [iterations] [repetitions]
// Prints one line per repetition: "<seconds> <updates_per_second>".
#include <chrono>
#include <cstdlib>
#include <iostream>

#include "swarmforge/motion/differential_drive.hpp"

int main(int argc, char** argv) {
    const long iterations = argc > 1 ? std::atol(argv[1]) : 5000000;
    const int reps = argc > 2 ? std::atoi(argv[2]) : 7;
    swarmforge::DifferentialDrive drive(0.05, 0.30);
    volatile double sink = 0.0;
    for (int r = -1; r < reps; ++r) {  // r = -1 is a warm-up run and is not reported
        swarmforge::Pose2D p{0, 0, 0};
        const auto t0 = std::chrono::steady_clock::now();
        for (long i = 0; i < iterations; ++i) p = drive.update(p, 0.5, 0.2, 0.001);
        const double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
        sink = sink + p.x;
        if (r >= 0) std::cout << s << " " << static_cast<double>(iterations) / s << "\n";
    }
    return 0;
}
