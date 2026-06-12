#include "wang_liu.h"
#include <queue>
#include <tuple>
#include <algorithm>

static const int DI[] = {-1, -1, -1, 0, 0, 1, 1, 1};
static const int DJ[] = {-1,  0,  1,-1, 1,-1, 0, 1};

Grid fillPits(const Grid& dem, double nodata) {
    int rows = dem.size();
    int cols = dem[0].size();

    Grid filled = dem;
    std::vector<std::vector<bool>> closed(rows, std::vector<bool>(cols, false));

    using Cell = std::tuple<double, int, int>;
    std::priority_queue<Cell, std::vector<Cell>, std::greater<Cell>> open;

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            bool border = (i == 0 || i == rows - 1 || j == 0 || j == cols - 1);
            if (border && dem[i][j] != nodata) {
                open.push({filled[i][j], i, j});
                closed[i][j] = true;
            }
        }
    }

    while (!open.empty()) {
        auto [e, i, j] = open.top();
        open.pop();

        for (int d = 0; d < 8; d++) {
            int ni = i + DI[d];
            int nj = j + DJ[d];

            if (ni < 0 || ni >= rows || nj < 0 || nj >= cols) continue;
            if (closed[ni][nj]) continue;
            if (filled[ni][nj] == nodata) continue;

            filled[ni][nj] = std::max(filled[ni][nj], e);
            open.push({filled[ni][nj], ni, nj});
            closed[ni][nj] = true;
        }
    }

    return filled;
}
