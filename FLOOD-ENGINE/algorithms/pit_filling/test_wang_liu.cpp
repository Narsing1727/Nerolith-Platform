#include "wang_liu.h"
#include <iostream>
#include <cassert>

void printGrid(const Grid& g) {
    for (auto& row : g) {
        for (double v : row) std::cout << v << "\t";
        std::cout << "\n";
    }
}

int main() {
    Grid dem = {
        {10, 10, 10, 10, 10},
        {10,  3,  3,  3, 10},
        {10,  3,  1,  3, 10},
        {10,  3,  3,  3, 10},
        {10, 10, 10, 10, 10}
    };

    std::cout << "=== Input DEM (pit at centre = 1.0) ===\n";
    printGrid(dem);

    Grid filled = fillPits(dem);

    std::cout << "\n=== Filled DEM ===\n";
    printGrid(filled);

    for (int i = 0; i < 5; i++)
        for (int j = 0; j < 5; j++)
            assert(filled[i][j] >= dem[i][j]);

    assert(filled[2][2] > dem[2][2]);

    std::cout << "\n=== Nodata test ===\n";
    Grid demNodata = {
        {10,    10,    10},
        {10, -9999,    10},
        {10,    10,    10}
    };
    Grid filledNodata = fillPits(demNodata);
    assert(filledNodata[1][1] == -9999);
    std::cout << "Nodata cell unchanged: OK\n";

    std::cout << "\nAll assertions passed.\n";
    return 0;
}
