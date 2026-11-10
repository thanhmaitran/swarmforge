// Optional pybind11 module `swarmforge._core` (built when pybind11 is available).
#include <pybind11/pybind11.h>

#include "swarmforge/geometry/geometry_utils.hpp"
#include "swarmforge/motion/differential_drive.hpp"

namespace py = pybind11;
using namespace swarmforge;

PYBIND11_MODULE(_core, m) {
    m.doc() = "SwarmForge C++ kernels";
    py::class_<Pose2D>(m, "Pose2D")
        .def(py::init<double, double, double>(), py::arg("x") = 0.0, py::arg("y") = 0.0,
             py::arg("theta") = 0.0)
        .def_readwrite("x", &Pose2D::x)
        .def_readwrite("y", &Pose2D::y)
        .def_readwrite("theta", &Pose2D::theta);
    py::class_<DifferentialDrive>(m, "DifferentialDrive")
        .def(py::init<double, double>(), py::arg("wheel_radius"), py::arg("wheel_base"))
        .def("update", &DifferentialDrive::update, py::arg("pose"), py::arg("linear_velocity"),
             py::arg("angular_velocity"), py::arg("dt"));
    m.def("normalize_angle", &normalize_angle);
}
