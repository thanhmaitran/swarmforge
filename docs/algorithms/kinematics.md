# Differential-drive kinematics

\[ \dot x = v\cos\theta,\quad \dot y = v\sin\theta,\quad \dot\theta = \omega \]
Forward Euler with fixed \(\Delta t\): \(x_{t+\Delta t} = x_t + v\cos\theta_t\,\Delta t\) (same for \(y\)),
\(\theta_{t+\Delta t} = \text{wrap}(\theta_t + \omega\Delta t)\) with wrap to \((-\pi, \pi]\).
Wheels (radius \(r\), base \(L\)): \(v = \tfrac r2(\omega_R+\omega_L)\), \(\omega = \tfrac rL(\omega_R-\omega_L)\).

Implementations: Python reference (`motion/kinematics.py`) and C++20 (`cpp/`) exposed through a C ABI + `ctypes`
(always built) and an optional pybind11 module `_core`. A test checks both on random inputs (agreement to 1e-12).
Euler integration is first-order: it drifts on long arcs with large \(\Delta t\); it is adequate for the small time
steps used here.
