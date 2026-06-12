#include "manning.h"
#include <cmath>
#include <algorithm>

static double computeSlope(const Grid& dem, int i, int j, double cellSize) {
    int rows = dem.size();
    int cols = dem[0].size();

    double dzdx, dzdy;

    if (j == 0)           dzdx = (dem[i][j+1] - dem[i][j])   / cellSize;
    else if (j == cols-1) dzdx = (dem[i][j]   - dem[i][j-1]) / cellSize;
    else                  dzdx = (dem[i][j+1] - dem[i][j-1]) / (2.0 * cellSize);

    if (i == 0)           dzdy = (dem[i+1][j] - dem[i][j])   / cellSize;
    else if (i == rows-1) dzdy = (dem[i][j]   - dem[i-1][j]) / cellSize;
    else                  dzdy = (dem[i+1][j] - dem[i-1][j]) / (2.0 * cellSize);

    return std::sqrt(dzdx * dzdx + dzdy * dzdy);
}

double manningVelocity(double n, double depth, double slope) {
    depth = std::max(depth, 1e-6);
    slope = std::max(slope, 1e-6);
    n     = std::max(n,     1e-6);
    return (1.0 / n) * std::pow(depth, 2.0 / 3.0) * std::sqrt(slope);
}

double rationalDischarge(double C, double rainfallIntensity, double flowAcc, double cellSize) {
    double intensityMs = rainfallIntensity / (1000.0 * 3600.0);
    double area = flowAcc * cellSize * cellSize;
    return C * intensityMs * area;
}

Grid computeFloodDepth(const Grid& dem, const IntGrid& flowAcc,
                       double rainfall, double C, double n,
                       double cellSize) {
    int rows = dem.size();
    int cols = dem[0].size();

    Grid depth(rows, std::vector<double>(cols, 0.0));

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            double slope = computeSlope(dem, i, j, cellSize);
            slope = std::max(slope, 1e-4);

            double Q = rationalDischarge(C, rainfall, flowAcc[i][j], cellSize);

            double depthGuess = 0.1;
            for (int iter = 0; iter < 20; iter++) {
                double v = manningVelocity(n, depthGuess, slope);
                double width = cellSize;
                double newDepth = Q / (v * width);
                newDepth = std::max(newDepth, 1e-9);
                if (std::abs(newDepth - depthGuess) < 1e-6) break;
                depthGuess = newDepth;
            }

            depth[i][j] = depthGuess;
        }
    }

    return depth;
}
