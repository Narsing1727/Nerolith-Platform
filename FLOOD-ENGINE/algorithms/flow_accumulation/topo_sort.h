#pragma once
#include <vector>

using Grid = std::vector<std::vector<double>>;
using IntGrid = std::vector<std::vector<int>>;

IntGrid computeFlowAccTopoSort(const IntGrid& flowDir, int rows, int cols);