#include "topo_sort.h"
#include <queue>

static const int DI[] = {0, 1, 1,  1,  0, -1, -1, -1};
static const int DJ[] = {1, 1, 0, -1, -1, -1,  0,  1};

static bool inBounds(int i, int j, int rows, int cols) {
    return i >= 0 && i < rows && j >= 0 && j < cols;
}

static std::pair<int,int> nextCell(int i, int j, int dir) {
    if (dir < 0 || dir > 7) return {-1, -1};
    return {i + DI[dir], j + DJ[dir]};
}

IntGrid computeFlowAccTopoSort(const IntGrid& flowDir, int rows, int cols) {
    IntGrid inDegree(rows, std::vector<int>(cols, 0));
    IntGrid acc(rows, std::vector<int>(cols, 1));

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            auto [ni, nj] = nextCell(i, j, flowDir[i][j]);
            if (inBounds(ni, nj, rows, cols)) {
                inDegree[ni][nj]++;
            }
        }
    }

    std::queue<std::pair<int,int>> q;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (inDegree[i][j] == 0) {
                q.push({i, j});
            }
        }
    }

    while (!q.empty()) {
        auto [i, j] = q.front();
        q.pop();

        auto [ni, nj] = nextCell(i, j, flowDir[i][j]);
        if (inBounds(ni, nj, rows, cols)) {
            acc[ni][nj] += acc[i][j];
            inDegree[ni][nj]--;
            if (inDegree[ni][nj] == 0) {
                q.push({ni, nj});
            }
        }
    }

    return acc;
}