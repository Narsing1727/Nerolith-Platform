#pragma once
#include <vector>

using Grid = std::vector<std::vector<double>>;
using IntGrid = std::vector<std::vector<int>>;

IntGrid computeD8(const Grid& dem, double cellSize = 1.0);

std::pair<int,int> nextCell(int i, int j, int dir, int rows, int cols);
