#pragma once
#include <vector>

using Grid = std::vector<std::vector<double>>;

Grid fillPits(const Grid& dem, double nodata = -9999.0);
