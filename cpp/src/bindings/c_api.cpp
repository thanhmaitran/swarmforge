// Plain C ABI used from Python through ctypes (no pybind11 required).
#include <cstddef>
#include <exception>

#include "swarmforge/motion/differential_drive.hpp"

#if defined(_WIN32)
#define SF_API extern "C" __declspec(dllexport)
#else
#define SF_API extern "C" __attribute__((visibility("default")))
#endif

using swarmforge::DifferentialDrive;
using swarmforge::Pose2D;

// Returns 0 on success, 1 on invalid argument. out = {x, y, theta}.
SF_API int sf_diff_drive_update(double wheel_radius, double wheel_base, double x, double y, double theta,
                                double v, double w, double dt, double* out) {
    try {
        const Pose2D p = DifferentialDrive(wheel_radius, wheel_base).update({x, y, theta}, v, w, dt);
        out[0] = p.x;
        out[1] = p.y;
        out[2] = p.theta;
        return 0;
    } catch (const std::exception&) {
        return 1;
    }
}

// Integrates `steps` identical control steps and writes (steps + 1) poses (x, y, theta) to out.
SF_API int sf_diff_drive_integrate(double wheel_radius, double wheel_base, double x, double y, double theta,
                                   double v, double w, double dt, std::size_t steps, double* out) {
    try {
        const DifferentialDrive model(wheel_radius, wheel_base);
        Pose2D p{x, y, theta};
        out[0] = p.x;
        out[1] = p.y;
        out[2] = p.theta;
        for (std::size_t i = 1; i <= steps; ++i) {
            p = model.update(p, v, w, dt);
            out[3 * i] = p.x;
            out[3 * i + 1] = p.y;
            out[3 * i + 2] = p.theta;
        }
        return 0;
    } catch (const std::exception&) {
        return 1;
    }
}

SF_API double sf_normalize_angle(double theta);

#include "swarmforge/geometry/geometry_utils.hpp"
SF_API double sf_normalize_angle(double theta) { return swarmforge::normalize_angle(theta); }
