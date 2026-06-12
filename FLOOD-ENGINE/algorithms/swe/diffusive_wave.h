#pragma once
#include <vector>
#include <functional>

using Grid = std::vector<std::vector<double>>;

struct SWEParams {
    double manningN  = 0.035;
    double rainfall  = 0.0;
    double cellSize  = 1.0;
    double totalTime = 3600.0;
    double cfl       = 0.5;
};

Grid runDiffusiveWave(const Grid& dem, const SWEParams& params,
                      std::function<void(int step, double t, const Grid& h)> onStep = nullptr);
