#include "d8.h"
#include <cmath>
#include <limits>

static const int DI[] = { 0,  1,  1,  1,  0, -1, -1, -1};
static const int DJ[] = { 1,  1,  0, -1, -1, -1,  0,  1};

static const bool DIAGONAL[] = {false, true, false, true, false, true, false, true};

IntGrid computeD8(const Grid& dem, double cellSize) {
    int rows = dem.size();
    int cols = dem[0].size();

    double diagDist = std::sqrt(2.0) * cellSize;

    IntGrid flowDir(rows, std::vector<int>(cols, -1));

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            double maxSlope = 0.0;
            int bestDir = -1;

            for (int d = 0; d < 8; d++) {
                int ni = i + DI[d];
                int nj = j + DJ[d];

                if (ni < 0 || ni >= rows || nj < 0 || nj >= cols) continue;

                double dist = DIAGONAL[d] ? diagDist : cellSize;
                double slope = (dem[i][j] - dem[ni][nj]) / dist;

                if (slope > maxSlope) {
                    maxSlope = slope;
                    bestDir = d;
                }
            }

            flowDir[i][j] = bestDir;
        }
    }

    return flowDir;
}

std::pair<int,int> nextCell(int i, int j, int dir, int rows, int cols) {
    if (dir < 0 || dir > 7) return {-1, -1};
    int ni = i + DI[dir];
    int nj = j + DJ[dir];
    if (ni < 0 || ni >= rows || nj < 0 || nj >= cols) return {-1, -1};
    return {ni, nj};
}
