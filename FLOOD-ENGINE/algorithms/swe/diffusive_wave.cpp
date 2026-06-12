#include "diffusive_wave.h"
#include <cmath>
#include <algorithm>
#include <stdexcept>

static const double G = 9.81;

static const int DI4[] = {-1,  1,  0,  0};
static const int DJ4[] = { 0,  0, -1,  1};

static double computeDt(const Grid& h, double cellSize, double cfl) {
    double hMax = 1e-6;
    for (auto& row : h)
        for (double v : row)
            hMax = std::max(hMax, v);
    return cfl * cellSize / std::sqrt(G * hMax);
}

static double computeFlux(double hi, double hj, double Wi, double Wj,
                           double n, double cellSize) {
    double S = (Wi - Wj) / cellSize;
    if (std::abs(S) < 1e-10) return 0.0;

    double hFace = std::max(hi, hj);
    if (hFace < 1e-6) return 0.0;

    double q = (std::pow(hFace, 5.0 / 3.0) / n) * std::sqrt(std::abs(S));
    return std::copysign(q, S);
}

Grid runDiffusiveWave(const Grid& dem, const SWEParams& params,
                      std::function<void(int step, double t, const Grid& h)> onStep) {
    int rows = dem.size();
    int cols = dem[0].size();

    if (rows < 3 || cols < 3)
        throw std::invalid_argument("DEM must be at least 3x3");

    double n        = params.manningN;
    double r        = params.rainfall / (1000.0 * 3600.0);
    double dx       = params.cellSize;
    double tTotal   = params.totalTime;
    double cfl      = params.cfl;

    Grid h(rows, std::vector<double>(cols, 0.0));
    Grid hNew = h;

    double t    = 0.0;
    int    step = 0;

    while (t < tTotal) {
        double dt = computeDt(h, dx, cfl);
        dt = std::min(dt, tTotal - t);
        dt = std::max(dt, 1e-3);

        Grid W(rows, std::vector<double>(cols, 0.0));
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
                W[i][j] = h[i][j] + dem[i][j];

        for (int i = 1; i < rows - 1; i++) {
            for (int j = 1; j < cols - 1; j++) {
                double netFlux = 0.0;

                for (int d = 0; d < 4; d++) {
                    int ni = i + DI4[d];
                    int nj = j + DJ4[d];
                    double q = computeFlux(h[i][j], h[ni][nj],
                                           W[i][j], W[ni][nj],
                                           n, dx);
                    netFlux -= q;
                }

                hNew[i][j] = h[i][j] + dt * (r - netFlux / dx);
                hNew[i][j] = std::max(hNew[i][j], 0.0);
            }
        }

        for (int i = 0; i < rows; i++) {
            hNew[i][0]      = 0.0;
            hNew[i][cols-1] = 0.0;
        }
        for (int j = 0; j < cols; j++) {
            hNew[0][j]      = 0.0;
            hNew[rows-1][j] = 0.0;
        }

        h = hNew;
        t += dt;
        step++;

        if (onStep) onStep(step, t, h);
    }

    return h;
}
