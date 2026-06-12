#pragma once
#include <vector>

using Grid = std::vector<std::vector<double>>;

Grid blendDepths(const Grid& physicsDepth, const Grid& mlDepth,
                 double alpha = 0.7);

double blendCell(double physicsVal, double mlVal, double alpha);
