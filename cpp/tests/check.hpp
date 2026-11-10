// Tiny dependency-free test harness so the C++ tests build offline (see ADR-0001 notes).
#pragma once

#include <cmath>
#include <functional>
#include <iostream>
#include <string>
#include <vector>

namespace sf_test {
struct Case {
    std::string name;
    std::function<void()> fn;
};
inline std::vector<Case>& registry() {
    static std::vector<Case> r;
    return r;
}
struct Registrar {
    Registrar(const std::string& n, std::function<void()> f) { registry().push_back({n, std::move(f)}); }
};
struct Failure {
    std::string msg;
};
}  // namespace sf_test

#define TEST(name)                                                       \
    static void name();                                                  \
    static sf_test::Registrar registrar_##name(#name, name);             \
    static void name()

#define CHECK(cond) \
    do { if (!(cond)) throw sf_test::Failure{std::string(__FILE__) + ":" + std::to_string(__LINE__) + " CHECK(" #cond ")"}; } while (0)

#define CHECK_NEAR(a, b, tol) \
    do { if (!(std::fabs((a) - (b)) <= (tol))) throw sf_test::Failure{std::string(__FILE__) + ":" + std::to_string(__LINE__) + " CHECK_NEAR(" #a ", " #b ")"}; } while (0)

#define CHECK_THROWS(expr)                                                                          \
    do {                                                                                           \
        bool threw_ = false;                                                                       \
        try { (void)(expr); } catch (const std::exception&) { threw_ = true; }                     \
        if (!threw_) throw sf_test::Failure{std::string(__FILE__) + ":" + std::to_string(__LINE__) + " CHECK_THROWS(" #expr ")"}; \
    } while (0)

#define SF_TEST_MAIN()                                                                \
    int main() {                                                                      \
        int failed = 0;                                                               \
        for (const auto& c : sf_test::registry()) {                                   \
            try { c.fn(); std::cout << "[ OK ] " << c.name << "\n"; }                 \
            catch (const sf_test::Failure& f) { ++failed; std::cout << "[FAIL] " << c.name << ": " << f.msg << "\n"; } \
            catch (const std::exception& e) { ++failed; std::cout << "[FAIL] " << c.name << ": exception " << e.what() << "\n"; } \
        }                                                                             \
        std::cout << sf_test::registry().size() - failed << "/" << sf_test::registry().size() << " passed\n"; \
        return failed == 0 ? 0 : 1;                                                   \
    }
