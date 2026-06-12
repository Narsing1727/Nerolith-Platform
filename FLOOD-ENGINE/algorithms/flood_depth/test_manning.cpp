#include "manning.h"
#include <iostream>
#include <cassert>
#include <cmath>

int main() {
    std::cout << "=== Test 1: Manning velocity increases with slope ===\n";
    double v1 = manningVelocity(0.035, 1.0, 0.01);
    double v2 = manningVelocity(0.035, 1.0, 0.05);
    std::cout << "v (slope=0.01): " << v1 << " m/s\n";
    std::cout << "v (slope=0.05): " << v2 << " m/s\n";
    assert(v2 > v1);

    std::cout << "\n=== Test 2: Manning velocity increases with depth ===\n";
    double va = manningVelocity(0.035, 0.5, 0.01);
    double vb = manningVelocity(0.035, 2.0, 0.01);
    std::cout << "v (depth=0.5m): " << va << " m/s\n";
    std::cout << "v (depth=2.0m): " << vb << " m/s\n";
    assert(vb > va);

    std::cout << "\n=== Test 3: Rougher surface = slower velocity ===\n";
    double v_concrete = manningVelocity(0.013, 1.0, 0.01);
    double v_forest   = manningVelocity(0.120, 1.0, 0.01);
    std::cout << "v concrete (n=0.013): " << v_concrete << " m/s\n";
    std::cout << "v forest   (n=0.120): " << v_forest   << " m/s\n";
    assert(v_concrete > v_forest);

    std::cout << "\n=== Test 4: Higher accumulation = deeper flood ===\n";
    Grid dem = {
        {10, 8, 6},
        { 8, 6, 4},
        { 6, 4, 2}
    };
    IntGrid accLow = {
        {1, 1, 1},
        {1, 2, 1},
        {1, 2, 3}
    };
    IntGrid accHigh = {
        {1,  2,  3},
        {2,  5,  4},
        {3, 10, 15}
    };

    Grid depthLow  = computeFloodDepth(dem, accLow,  50.0, 0.7, 0.035, 30.0);
    Grid depthHigh = computeFloodDepth(dem, accHigh, 50.0, 0.7, 0.035, 30.0);

    std::cout << "Low acc depth  [2][2]: " << depthLow[2][2]  << " m\n";
    std::cout << "High acc depth [2][2]: " << depthHigh[2][2] << " m\n";
    assert(depthHigh[2][2] > depthLow[2][2]);

    std::cout << "\n=== Test 5: No nan or negative depths ===\n";
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++) {
            assert(!std::isnan(depthHigh[i][j]));
            assert(depthHigh[i][j] >= 0.0);
        }
    std::cout << "All depths valid: OK\n";

    std::cout << "\nAll assertions passed.\n";
    return 0;
}
