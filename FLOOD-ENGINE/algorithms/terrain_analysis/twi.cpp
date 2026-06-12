#include "twi.h"
#include <cmath>
#include <algorithm>

static double computeSlope(const Grid& dem, int i, int j, double cellSize) {
    int rows = dem.size();
    int cols = dem[0].size();

    double dzdx, dzdy;

    if (j == 0)
        dzdx = (dem[i][j+1] - dem[i][j]) / cellSize;
    else if (j == cols - 1)
        dzdx = (dem[i][j] - dem[i][j-1]) / cellSize;
    else
        dzdx = (dem[i][j+1] - dem[i][j-1]) / (2.0 * cellSize);

    if (i == 0)
        dzdy = (dem[i+1][j] - dem[i][j]) / cellSize;
    else if (i == rows - 1)
        dzdy = (dem[i][j] - dem[i-1][j]) / cellSize;
    else
        dzdy = (dem[i+1][j] - dem[i-1][j]) / (2.0 * cellSize);

    return std::sqrt(dzdx * dzdx + dzdy * dzdy);
}

Grid computeTWI(const Grid& dem, const IntGrid& flowAcc, double cellSize) {
    int rows = dem.size();
    int cols = dem[0].size();

    Grid twi(rows, std::vector<double>(cols, 0.0));

    double minSlope = 0.001;

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            double area = flowAcc[i][j] * cellSize * cellSize;
            double slope = computeSlope(dem, i, j, cellSize);
            slope = std::max(slope, minSlope);
            twi[i][j] = std::log(area / std::tan(std::atan(slope)));
        }
    }

    return twi;
}
