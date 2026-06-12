#include <iostream>
#include "raster.h"
using namespace std;

int main() {
    Raster dem;
    if (!dem.loadCSVFile("dem3.csv")) {
        cout << "DEM load failed\n";
        return 1;
    }

    cout << "DEM loaded: " << dem.getRows() << "x" << dem.getCols() << "\n";
    cout << "Elevation min: " << dem.getMin() << " max: " << dem.getMax() << "\n";

    auto fa = dem.computeFlowAccumulation();
    int maxAcc = 0;
    for (auto& row : fa)
        for (int v : row)
            if (v > maxAcc) maxAcc = v;
    cout << "Flow accumulation max: " << maxAcc << "\n";

    auto twi = dem.computeTWI(30.0);
    double twiMin = twi[0][0], twiMax = twi[0][0];
    for (auto& row : twi)
        for (double v : row) {
            if (v > twiMax) twiMax = v;
            if (v < twiMin) twiMin = v;
        }
    cout << "TWI min: " << twiMin << " max: " << twiMax << "\n";

    auto depth = dem.FloodDepthGridFinal(100.0, 30.0);
    double dMin = depth[0][0], dMax = depth[0][0];
    for (auto& row : depth)
        for (double v : row) {
            if (v > dMax) dMax = v;
            if (v < dMin) dMin = v;
        }
    cout << "Flood depth min: " << dMin << " max: " << dMax << "\n";

    dem.exportGridCSV(depth, "depth_out.csv");
    dem.exportGridCSV(twi,   "twi_out.csv");
    cout << "Exported depth_out.csv and twi_out.csv\n";

    return 0;
}