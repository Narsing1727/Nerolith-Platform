#include "twi.h"
#include <iostream>
#include <cassert>
#include <cmath>

void printGrid(const Grid& g, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            std::cout << g[i][j] << "\t";
        }
        std::cout << "\n";
    }
}

int main() {
    int rows = 3, cols = 3;

    Grid dem = {
        {10, 8, 6},
        { 8, 6, 4},
        { 6, 4, 2}
    };

    IntGrid flowAcc = {
        {1, 1, 1},
        {2, 3, 2},
        {3, 6, 4}
    };

    std::cout << "=== Test 1: Basic TWI computation ===\n";
    Grid twi = computeTWI(dem, flowAcc, 1.0);
    printGrid(twi, rows, cols);

    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            assert(!std::isnan(twi[i][j]) && !std::isinf(twi[i][j]));

    std::cout << "\n=== Test 2: Valley cell has higher TWI than ridge cell ===\n";
    Grid dem2 = {
        {20, 15, 10},
        {15,  8,  5},
        {10,  5,  1}
    };
    IntGrid flowAcc2 = {
        { 1,  1,  2},
        { 2,  5,  4},
        { 4, 10, 15}
    };
    Grid twi2 = computeTWI(dem2, flowAcc2, 30.0);

    double ridgeTWI  = twi2[0][0];
    double valleyTWI = twi2[2][2];
    std::cout << "Ridge  TWI [0][0]: " << ridgeTWI  << "\n";
    std::cout << "Valley TWI [2][2]: " << valleyTWI << "\n";
    assert(valleyTWI > ridgeTWI);

    std::cout << "\n=== Test 3: Flat cell clamped (no division by zero) ===\n";
    Grid demFlat = {
        {5, 5, 5},
        {5, 5, 5},
        {5, 5, 5}
    };
    IntGrid accFlat = {
        {1, 1, 1},
        {1, 1, 1},
        {1, 1, 1}
    };
    Grid twiFlat = computeTWI(demFlat, accFlat, 1.0);
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            assert(!std::isinf(twiFlat[i][j]) && !std::isnan(twiFlat[i][j]));
    std::cout << "No inf/nan on flat DEM: OK\n";

    std::cout << "\nAll assertions passed.\n";
    return 0;
}
