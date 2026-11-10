#pragma once

#include <cmath>

namespace swarmforge {

struct Vector2 {
    double x{};
    double y{};

    constexpr Vector2 operator+(const Vector2& o) const { return {x + o.x, y + o.y}; }
    constexpr Vector2 operator-(const Vector2& o) const { return {x - o.x, y - o.y}; }
    constexpr Vector2 operator*(double s) const { return {x * s, y * s}; }
    constexpr double dot(const Vector2& o) const { return x * o.x + y * o.y; }
    constexpr double cross(const Vector2& o) const { return x * o.y - y * o.x; }
    double norm() const { return std::hypot(x, y); }
};

}  // namespace swarmforge
