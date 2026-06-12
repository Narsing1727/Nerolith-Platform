#pragma once
#include <vector>

using Grid = std::vector<std::vector<double>>;
using IntGrid = std::vector<std::vector<int>>;

Grid computeTWI(const Grid& dem, const IntGrid& flowAcc, double cellSize = 1.0);
