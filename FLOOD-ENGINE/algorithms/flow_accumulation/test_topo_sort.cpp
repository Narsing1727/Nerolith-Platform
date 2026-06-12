#include "topo_sort.h"
#include <iostream>
#include <cassert>

int main() {
    int rows = 3, cols = 3;

    IntGrid flowDir = {
        {2, 2, 2},
        {2, 2, 2},
        {-1,-1,-1}
    };

    IntGrid acc = computeFlowAccTopoSort(flowDir, rows, cols);

    std::cout << "Flow accumulation grid:\n";
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            std::cout << acc[i][j] << " ";
        }
        std::cout << "\n";
    }

    assert(acc[0][0] == 1);
    assert(acc[0][1] == 1);
    assert(acc[0][2] == 1);
    assert(acc[1][0] == 2);
    assert(acc[1][1] == 2);
    assert(acc[1][2] == 2);
    assert(acc[2][0] == 3);
    assert(acc[2][1] == 3);
    assert(acc[2][2] == 3);

    std::cout << "\nAll assertions passed.\n";
    return 0;
}