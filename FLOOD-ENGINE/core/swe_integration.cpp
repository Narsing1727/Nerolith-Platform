#include "raster.h"
#include <cmath>
#include <algorithm>
#include <functional>

// Diffusive wave SWE wired into Raster.
// Uses the same Manning-based flux formula from algorithms/swe/diffusive_wave.cpp
// but reads directly from Raster::grid (the DEM) and adds rainfall source term.

static const double G = 9.81;

static double computeSafeDt(const std::vector<std::vector<double>>& h,
                             int rows, int cols, double cellSize)
{
    double hmax = 0.0;
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            if (h[i][j] > hmax) hmax = h[i][j];

    if (hmax < 1e-6) return 1.0;
    double dt = 0.5 * cellSize / std::sqrt(G * hmax);
    return std::max(0.01, std::min(dt, 5.0));
}

static double manningFlux(double h_up, double h_dn,
                           double z_up, double z_dn,
                           double cellSize, double n)
{
    double S = (z_up + h_up - z_dn - h_dn) / cellSize;
    if (std::abs(S) < 1e-10) return 0.0;

    double h_face = std::max(h_up, h_dn);
    if (h_face < 1e-6)  return 0.0;

    double q = (1.0 / n) * std::pow(h_face, 5.0 / 3.0) * std::sqrt(std::abs(S));
    return std::copysign(q, S);
}

std::vector<std::vector<double>> Raster::runSWE(
    double rainfall,
    double totalSeconds,
    double manningN,
    double cellSize,
    std::function<void(const std::vector<std::vector<double>>&, double)> onStep
) const
{
  
    double rainMs = (rainfall / 1000.0) / 3600.0;

    std::vector<std::vector<double>> h(rows, std::vector<double>(cols, 0.0));

    double elapsed = 0.0;

    while (elapsed < totalSeconds) {
        double dt = computeSafeDt(h, rows, cols, cellSize);
        if (elapsed + dt > totalSeconds) dt = totalSeconds - elapsed;

        std::vector<std::vector<double>> dh(rows, std::vector<double>(cols, 0.0));

        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
                dh[i][j] += rainMs * dt;

        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols - 1; j++) {
                double q = manningFlux(h[i][j], h[i][j+1],
                                       grid[i][j], grid[i][j+1],
                                       cellSize, manningN);
                double dv = q * dt / cellSize;
                dh[i][j]   -= dv;
                dh[i][j+1] += dv;
            }
        }

        for (int i = 0; i < rows - 1; i++) {
            for (int j = 0; j < cols; j++) {
                double q = manningFlux(h[i][j], h[i+1][j],
                                       grid[i][j], grid[i+1][j],
                                       cellSize, manningN);
                double dv = q * dt / cellSize;
                dh[i][j]   -= dv;
                dh[i+1][j] += dv;
            }
        }
        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                h[i][j] += dh[i][j];
                if (h[i][j] < 0.0) h[i][j] = 0.0;
            }
        }
     
        for (int i = 0; i < rows; i++) { h[i][0] = 0.0; h[i][cols-1] = 0.0; }
        for (int j = 0; j < cols; j++) { h[0][j] = 0.0; h[rows-1][j] = 0.0; }

        elapsed += dt;

        if (onStep) onStep(h, elapsed);
    }

    return h;
}