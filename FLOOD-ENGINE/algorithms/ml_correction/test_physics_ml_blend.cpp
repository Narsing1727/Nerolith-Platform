#include "physics_ml_blend.h"
#include <iostream>
#include <cassert>
#include <cmath>
#include <stdexcept>

int main() {
    std::cout << "=== Test 1: Basic blend alpha=0.7 ===\n";
    double result = blendCell(2.0, 4.0, 0.7);
    double expected = 0.7 * 4.0 + 0.3 * 2.0;
    std::cout << "physics=2.0  ml=4.0  blended=" << result << "  expected=" << expected << "\n";
    assert(std::abs(result - expected) < 1e-9);

    std::cout << "\n=== Test 2: alpha=0 means pure physics ===\n";
    double r2 = blendCell(2.0, 99.0, 0.0);
    std::cout << "alpha=0: " << r2 << " (expect 2.0)\n";
    assert(std::abs(r2 - 2.0) < 1e-9);

    std::cout << "\n=== Test 3: alpha=1 means pure ML ===\n";
    double r3 = blendCell(99.0, 5.0, 1.0);
    std::cout << "alpha=1: " << r3 << " (expect 5.0)\n";
    assert(std::abs(r3 - 5.0) < 1e-9);

    std::cout << "\n=== Test 4: Negative ML clamped to zero ===\n";
    double r4 = blendCell(2.0, -3.0, 0.7);
    std::cout << "ml=-3.0 clamped result: " << r4 << " (expect >= 0)\n";
    assert(r4 >= 0.0);

    std::cout << "\n=== Test 5: Full grid blend ===\n";
    Grid physics = {{1.0, 2.0}, {3.0, 4.0}};
    Grid ml      = {{2.0, 4.0}, {6.0, 8.0}};
    Grid blended = blendDepths(physics, ml, 0.7);

    for (int i = 0; i < 2; i++)
        for (int j = 0; j < 2; j++) {
            double exp = 0.7 * ml[i][j] + 0.3 * physics[i][j];
            assert(std::abs(blended[i][j] - exp) < 1e-9);
        }
    std::cout << "Grid blend correct: OK\n";

    std::cout << "\n=== Test 6: Mismatched grids throw ===\n";
    Grid small = {{1.0}};
    bool threw = false;
    try {
        blendDepths(physics, small, 0.7);
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    assert(threw);
    std::cout << "Exception on mismatched grids: OK\n";

    std::cout << "\n=== Test 7: Invalid alpha throws ===\n";
    bool threw2 = false;
    try {
        blendDepths(physics, ml, 1.5);
    } catch (const std::invalid_argument&) {
        threw2 = true;
    }
    assert(threw2);
    std::cout << "Exception on alpha > 1: OK\n";

    std::cout << "\nAll assertions passed.\n";
    return 0;
}
