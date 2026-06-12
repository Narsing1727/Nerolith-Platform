#include "d8.h"
#include <iostream>
#include <cassert>

int main() {
    Grid dem = {
        {9, 8, 7},
        {6, 5, 4},
        {3, 2, 1}
    };

    std::cout << "=== Test 1: Slope flows to bottom-right corner ===\n";
    IntGrid dir = computeD8(dem, 1.0);

    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            std::cout << dir[i][j] << " ";
        }
        std::cout << "\n";
    }

    auto [ni, nj] = nextCell(0, 0, dir[0][0], 3, 3);
    std::cout << "Cell (0,0) flows to (" << ni << "," << nj << ")\n";
    assert(ni >= 0 && nj >= 0);
    assert(dem[ni][nj] < dem[0][0]);

    std::cout << "\n=== Test 2: Diagonal vs cardinal tie-breaking ===\n";
    Grid dem2 = {
        {10, 10, 10},
        {10,  5,  4},
        {10, 10, 10}
    };
    IntGrid dir2 = computeD8(dem2, 1.0);
    auto [ni2, nj2] = nextCell(1, 1, dir2[1][1], 3, 3);
    std::cout << "Centre flows to (" << ni2 << "," << nj2 << ")\n";
    assert(ni2 == 1 && nj2 == 2);

    std::cout << "\n=== Test 3: Diagonal correction matters ===\n";
    Grid dem3 = {
        {10, 10,  10},
        {10,  5,  10},
        {10, 10, 4.5}
    };
    IntGrid dirSmall = computeD8(dem3, 1.0);
    auto [ni3, nj3] = nextCell(1, 1, dirSmall[1][1], 3, 3);
    std::cout << "Centre (cellSize=1): flows to (" << ni3 << "," << nj3 << ")\n";

    std::cout << "\n=== Test 4: Pit returns -1 ===\n";
    Grid dem4 = {
        {5, 5, 5},
        {5, 1, 5},
        {5, 5, 5}
    };
    IntGrid dir4 = computeD8(dem4, 1.0);
    std::cout << "Pit cell dir: " << dir4[1][1] << " (expect -1 without pit filling)\n";
    assert(dir4[1][1] == -1);

    std::cout << "\nAll assertions passed.\n";
    return 0;
}
