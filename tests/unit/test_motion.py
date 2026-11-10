import math
import random

import pytest

from swarmforge.core.exceptions import ValidationError
from swarmforge.core.types import Pose, Velocity
from swarmforge.motion.kinematics import DifferentialDrive, normalize_angle
from swarmforge.motion.native import NativeDifferentialDrive, native_available
from swarmforge.motion.trajectory import integrate_trajectory
from swarmforge.motion.velocity_limiter import VelocityLimiter


def test_straight_line_and_rotation():
    d = DifferentialDrive(0.05, 0.30)
    p = Pose(0, 0, 0)
    for _ in range(10):
        p = d.update(p, 1.0, 0.0, 0.1)
    assert p.x == pytest.approx(1.0) and p.y == pytest.approx(0.0)
    q = d.update(Pose(1, 2, 0), 0.0, math.pi / 2, 1.0)
    assert (q.x, q.y) == (1, 2) and q.theta == pytest.approx(math.pi / 2)


def test_angle_normalisation_range():
    for k in range(-50, 50):
        t = normalize_angle(k * 0.7)
        assert -math.pi < t <= math.pi
    assert normalize_angle(math.pi) == pytest.approx(math.pi)
    assert normalize_angle(-math.pi) == pytest.approx(math.pi)


def test_wheel_speed_roundtrip():
    d = DifferentialDrive(0.05, 0.30)
    wl, wr = d.wheel_speeds(0.5, 0.2)
    v = d.body_velocity(wl, wr)
    assert v.linear == pytest.approx(0.5) and v.angular == pytest.approx(0.2)


def test_invalid_inputs():
    with pytest.raises(ValidationError):
        DifferentialDrive(0.0, 0.3)
    with pytest.raises(ValidationError):
        DifferentialDrive(0.05, 0.3).update(Pose(0, 0, 0), 1, 0, -0.1)


def test_velocity_limiter():
    lim = VelocityLimiter(1.0, 0.5, 2.0)
    out = lim.limit(Velocity(0, 0), Velocity(5, 5), 0.1)
    assert out.linear == pytest.approx(0.05) and abs(out.angular) <= 2.0
    v = Velocity(0, 0)
    for _ in range(100):
        v = lim.limit(v, Velocity(5, 0), 0.1)
    assert v.linear == pytest.approx(1.0)


def test_trajectory_length():
    poses = integrate_trajectory(DifferentialDrive(0.05, 0.3), Pose(0, 0, 0), [Velocity(1, 0)] * 5, 0.1)
    assert len(poses) == 6 and poses[-1].x == pytest.approx(0.5)


def test_python_matches_cpp_reference():
    if not native_available():
        pytest.skip("native kernels not built (python -m swarmforge.motion.native --build)")
    py, nat = DifferentialDrive(0.05, 0.30), NativeDifferentialDrive(0.05, 0.30)
    rng = random.Random(0)
    for _ in range(500):
        p = Pose(rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(-7, 7))
        v, w, dt = rng.uniform(-2, 2), rng.uniform(-3, 3), rng.uniform(0, 0.5)
        a, b = py.update(p, v, w, dt), nat.update(p, v, w, dt)
        assert (a.x, a.y, a.theta) == pytest.approx((b.x, b.y, b.theta), abs=1e-12)
    with pytest.raises(ValidationError):
        nat.update(Pose(0, 0, 0), 1, 0, -1)
    traj = nat.integrate(Pose(0, 0, 0), 0.5, 0.2, 0.1, 50)
    ref = integrate_trajectory(py, Pose(0, 0, 0), [Velocity(0.5, 0.2)] * 50, 0.1)
    assert traj[-1].theta == pytest.approx(ref[-1].theta, abs=1e-12)
