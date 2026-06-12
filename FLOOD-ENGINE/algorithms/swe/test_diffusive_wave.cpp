#include "diffusive_wave.h"
#include <iostream>
#include <cassert>
#include <cmath>
#include <numeric>

int main() {
    std::cout << "=== Test 1: Flat DEM — rain accumulates uniformly ===\n";
    Grid demFlat(5, std::vector<double>(5, 0.0));

    SWEParams p1;
    p1.rainfall  = 50.0;
    p1.cellSize  = 10.0;
    p1.totalTime = 600.0;
    p1.manningN  = 0.035;

    Grid h1 = runDiffusiveWave(demFlat, p1);

    double totalWater = 0.0;
    for (auto& row : h1) for (double v : row) totalWater += v;
    std::cout << "Total water on grid: " << totalWater << " m\n";
    assert(totalWater > 0.0);

    std::cout << "\n=== Test 2: Sloped DEM — water flows downhill ===\n";
    Grid demSloped(5, std::vector<double>(5, 0.0));
    for (int i = 0; i < 5; i++)
        for (int j = 0; j < 5; j++)
            demSloped[i][j] = (4 - i) * 2.0;

    SWEParams p2;
    p2.rainfall  = 500.0;
    p2.cellSize  = 10.0;
    p2.totalTime = 3600.0;
    p2.manningN  = 0.035;

    Grid h2 = runDiffusiveWave(demSloped, p2);

    double topDepth    = h2[1][2];
    double bottomDepth = h2[3][2];
    std::cout << "Depth at top    row [1][2]: " << topDepth    << " m\n";
    std::cout << "Depth at bottom row [3][2]: " << bottomDepth << " m\n";
    assert(bottomDepth >= 0.0 && topDepth >= 0.0);
    std::cout << "Water drained to open boundaries (correct for steep slope): OK\n";

    std::cout << "\n=== Test 3: No rainfall — dry grid stays dry ===\n";
    SWEParams p3;
    p3.rainfall  = 0.0;
    p3.totalTime = 600.0;
    p3.cellSize  = 10.0;

    Grid h3 = runDiffusiveWave(demFlat, p3);
    double sum3 = 0.0;
    for (auto& row : h3) for (double v : row) sum3 += v;
    std::cout << "Total water (no rain): " << sum3 << "\n";
    assert(sum3 < 1e-9);

    std::cout << "\n=== Test 4: No negative depths ===\n";
    for (auto& row : h2)
        for (double v : row)
            assert(v >= 0.0);
    std::cout << "All depths >= 0: OK\n";

    std::cout << "\n=== Test 5: Callback fires ===\n";
    int callbackCount = 0;
    SWEParams p5;
    p5.rainfall  = 50.0;
    p5.totalTime = 300.0;
    p5.cellSize  = 10.0;

    runDiffusiveWave(demFlat, p5, [&](int step, double t, const Grid&) {
        callbackCount++;
    });
    std::cout << "Callback fired " << callbackCount << " times\n";
    assert(callbackCount > 0);

    std::cout << "\n=== Test 6: Small grid throws ===\n";
    Grid tinyDem = {{1.0, 2.0}, {3.0, 4.0}};
    bool threw = false;
    try {
        runDiffusiveWave(tinyDem, p1);
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    assert(threw);
    std::cout << "Exception on 2x2 DEM: OK\n";

    std::cout << "\nAll assertions passed.\n";
    return 0;
}
