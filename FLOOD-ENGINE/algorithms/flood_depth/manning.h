#pragma once
#include <vector>

using Grid = std::vector<std::vector<double>>;
using IntGrid = std::vector<std::vector<int>>;

double manningVelocity(double n, double depth, double slope);

double rationalDischarge(double C, double rainfallIntensity, double flowAcc, double cellSize);

Grid computeFloodDepth(const Grid& dem, const IntGrid& flowAcc,
                       double rainfall, double C, double n,
                       double cellSize = 1.0);
