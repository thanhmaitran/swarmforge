"""ctypes bridge to the C++ kernels, with graceful fallback to the Python reference.

Search order for the shared library: ``$SWARMFORGE_NATIVE_LIB``, the package directory,
``<repo>/build/``. Build it with ``python -m swarmforge.motion.native --build`` (needs g++/clang++)
or with CMake (``cmake -S cpp -B build && cmake --build build``).
"""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

from swarmforge.core.exceptions import ValidationError
from swarmforge.core.types import Pose
from swarmforge.motion.kinematics import DifferentialDrive as PyDifferentialDrive

_LIBNAMES = {"win32": "swarmforge_native.dll", "darwin": "libswarmforge_native.dylib"}
LIB_NAME = _LIBNAMES.get(sys.platform, "libswarmforge_native.so")
REPO_ROOT = Path(__file__).resolve().parents[3]
_lib: ctypes.CDLL | None = None
_tried = False


def _candidates() -> list[Path]:
    out = []
    if os.environ.get("SWARMFORGE_NATIVE_LIB"):
        out.append(Path(os.environ["SWARMFORGE_NATIVE_LIB"]))
    here = Path(__file__).resolve().parents[1]
    out += [
        here / LIB_NAME,
        REPO_ROOT / "build" / LIB_NAME,
        REPO_ROOT / "build" / "Release" / LIB_NAME,
        REPO_ROOT / "build" / "native" / "Release" / LIB_NAME,
    ]
    return out


def load_library(force: bool = False) -> ctypes.CDLL | None:
    global _lib, _tried
    if _tried and not force:
        return _lib
    _tried, _lib = True, None
    for path in _candidates():
        if path.exists():
            try:
                lib = ctypes.CDLL(str(path))
            except OSError:
                continue
            dbl = ctypes.c_double
            lib.sf_diff_drive_update.argtypes = [dbl] * 8 + [ctypes.POINTER(dbl)]
            lib.sf_diff_drive_update.restype = ctypes.c_int
            lib.sf_diff_drive_integrate.argtypes = [dbl] * 8 + [ctypes.c_size_t, ctypes.POINTER(dbl)]
            lib.sf_diff_drive_integrate.restype = ctypes.c_int
            lib.sf_normalize_angle.argtypes = [dbl]
            lib.sf_normalize_angle.restype = dbl
            _lib = lib
            break
    return _lib


def native_available() -> bool:
    return load_library() is not None


def build_native(out_dir: Path | None = None) -> Path:
    """Compile the C++ kernels with g++/clang++ (a CMake-free convenience for development)."""
    cxx = shutil.which("g++") or shutil.which("clang++")
    if cxx is None:
        raise RuntimeError("no C++ compiler (g++/clang++) found; use CMake instead")
    out = (out_dir or REPO_ROOT / "build") / LIB_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    cpp = REPO_ROOT / "cpp"
    sources = [cpp / "src" / "geometry" / "geometry_utils.cpp", cpp / "src" / "motion" / "differential_drive.cpp",
               cpp / "src" / "bindings" / "c_api.cpp"]
    cmd = [cxx, "-std=c++20", "-O2", "-shared", "-fPIC", "-fvisibility=hidden", f"-I{cpp / 'include'}",
           *map(str, sources), "-o", str(out)]
    subprocess.run(cmd, check=True)
    load_library(force=True)
    return out


class NativeDifferentialDrive:
    """Same interface as :class:`swarmforge.motion.kinematics.DifferentialDrive`, backed by C++."""

    def __init__(self, wheel_radius: float, wheel_base: float) -> None:
        lib = load_library()
        if lib is None:
            raise RuntimeError("native library not available")
        if not wheel_radius > 0 or not wheel_base > 0:
            raise ValidationError("wheel_radius and wheel_base must be positive")
        self._lib, self.wheel_radius, self.wheel_base = lib, wheel_radius, wheel_base

    def update(self, pose: Pose, linear_velocity: float, angular_velocity: float, dt: float) -> Pose:
        out = (ctypes.c_double * 3)()
        rc = self._lib.sf_diff_drive_update(self.wheel_radius, self.wheel_base, pose.x, pose.y, pose.theta,
                                            linear_velocity, angular_velocity, dt, out)
        if rc != 0:
            raise ValidationError("invalid argument rejected by native kernel")
        return Pose(out[0], out[1], out[2])

    def integrate(self, pose: Pose, linear_velocity: float, angular_velocity: float, dt: float,
                  steps: int, as_poses: bool = True) -> list[Pose] | ctypes.Array:  # type: ignore[type-arg]
        out = (ctypes.c_double * (3 * (steps + 1)))()
        rc = self._lib.sf_diff_drive_integrate(self.wheel_radius, self.wheel_base, pose.x, pose.y, pose.theta,
                                               linear_velocity, angular_velocity, dt, steps, out)
        if rc != 0:
            raise ValidationError("invalid argument rejected by native kernel")
        if not as_poses:
            return out  # flat (x, y, theta) triples; avoids creating one Python object per pose
        return [Pose(out[3 * i], out[3 * i + 1], out[3 * i + 2]) for i in range(steps + 1)]


def get_drive(wheel_radius: float, wheel_base: float) -> PyDifferentialDrive | NativeDifferentialDrive:
    if native_available():
        return NativeDifferentialDrive(wheel_radius, wheel_base)
    return PyDifferentialDrive(wheel_radius, wheel_base)


if __name__ == "__main__":  # pragma: no cover
    if "--build" in sys.argv:
        print(build_native())
    print("native available:", native_available())
