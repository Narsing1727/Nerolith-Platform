#include "raster.h"
#include <iostream>
#include <cmath>
#include <fstream>
using namespace std;

static const int DI[8] = { 0,  1,  1,  1,  0, -1, -1, -1};
static const int DJ[8] = { 1,  1,  0, -1, -1, -1,  0,  1};
static const bool IS_DIAG[8] = {false, true, false, true, false, true, false, true};

int Raster::getFlowDirection(int i, int j) const {
    double maxSlope = 0.0;
    int bestDir = -1;

    for (int d = 0; d < 8; d++) {
        int ni = i + DI[d];
        int nj = j + DJ[d];

        if (ni < 0 || ni >= rows || nj < 0 || nj >= cols) continue;

        double dist  = IS_DIAG[d] ? std::sqrt(2.0) : 1.0;
        double slope = (grid[i][j] - grid[ni][nj]) / dist;

        if (slope > maxSlope) {
            maxSlope = slope;
            bestDir  = d;
        }
    }

    return bestDir;
}

vector<pair<int,int>> Raster::traceFlowPath(
    int i, int j,
    vector<vector<bool>>& visited
) const {
    vector<pair<int,int>> path;
    if (i < 0 || i >= rows || j < 0 || j >= cols) return path;
    if (visited[i][j]) return path;

    visited[i][j] = true;
    path.push_back({i, j});

    int dir = getFlowDirection(i, j);
    if (dir == -1) return path;

    auto nxt  = nextCell(i, j, dir);
    auto rest = traceFlowPath(nxt.first, nxt.second, visited);
    path.insert(path.end(), rest.begin(), rest.end());
    return path;
}

void Raster::exportFlowPathCSV(
    const string& filename,
    int si, int sj
) const {
    vector<vector<bool>> visited(rows, vector<bool>(cols, false));
    auto path = traceFlowPath(si, sj, visited);

    ofstream file(filename);
    if (!file.is_open()) { cout << "Error opening flow path CSV\n"; return; }

    file << "x,y,order\n";
    for (int k = 0; k < (int)path.size(); k++) {
        double x =  path[k].second + 0.5;
        double y = -(path[k].first  + 0.5);
        file << x << "," << y << "," << k << "\n";
    }
    file.close();
    cout << "Flow path CSV written: " << filename << endl;
}