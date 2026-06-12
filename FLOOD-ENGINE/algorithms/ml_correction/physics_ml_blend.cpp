#include "physics_ml_blend.h"
#include <algorithm>
#include <stdexcept>

double blendCell(double physicsVal, double mlVal, double alpha) {
    mlVal      = std::max(mlVal,      0.0);
    physicsVal = std::max(physicsVal, 0.0);
    double blended = alpha * mlVal + (1.0 - alpha) * physicsVal;
    return std::max(blended, 0.0);
}

Grid blendDepths(const Grid& physicsDepth, const Grid& mlDepth, double alpha) {
    int rows = physicsDepth.size();
    int cols = physicsDepth[0].size();

    if (mlDepth.size() != (size_t)rows || mlDepth[0].size() != (size_t)cols)
        throw std::invalid_argument("Grid dimensions must match");

    if (alpha < 0.0 || alpha > 1.0)
        throw std::invalid_argument("alpha must be between 0 and 1");

    Grid result(rows, std::vector<double>(cols, 0.0));

    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            result[i][j] = blendCell(physicsDepth[i][j], mlDepth[i][j], alpha);

    return result;
}
