#include "raster.h"
#include <cmath>
#include <algorithm>



std::vector<std::vector<double>> Raster::FloodDepthBlended(
    RandomForest& rf,
    double rainfall,
    double alpha,
    double cellSize,
    double manningN,
    double durationHr,
    double Ks,
    double psi,
    double dTheta
) const
{
    // clamp alpha to [0,1]
    if (alpha < 0.0) alpha = 0.0;
    if (alpha > 1.0) alpha = 1.0;

    // physics depth grid (Manning + Green-Ampt)
    auto physics = FloodDepthGridFinal(
        rainfall, cellSize, manningN, durationHr, Ks, psi, dTheta);

    
    auto fa  = computeFlowAccumulation();
    auto twi = computeTWI(cellSize);

    std::vector<std::vector<double>> blended(
        rows, std::vector<double>(cols, 0.0));

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            double slope = computeSlopeAt(i, j, cellSize);

            std::vector<double> features = {
                static_cast<double>(fa[i][j]),  // [0] flow acc
                grid[i][j],                      // [1] elevation
                slope,                           // [2] slope
                twi[i][j],                       // [3] TWI
                rainfall,                        // [4] rainfall mm/hr
                manningN                         // [5] Manning N
            };

            double depthML = rf.predict(features);
            if (depthML < 0.0) depthML = 0.0; 

            double depthPhysics = physics[i][j];

            blended[i][j] = alpha * depthML + (1.0 - alpha) * depthPhysics;
        }
    }

    return blended;
}