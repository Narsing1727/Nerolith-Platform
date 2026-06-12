#include "raster.h"
#include <iostream>
#include <fstream>
#include <cmath>
#include <algorithm>
using namespace std;
// flood stat;

double Raster::FloodMax(int t) const
{
    auto fa = FloodDepthGrid(t);
    double m = fa[0][0];
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            if (fa[i][j] > m)
                m = fa[i][j];
    return m;
}

double Raster::FloodMin(int t) const
{
    auto fa = FloodDepthGrid(t);
    double m = fa[0][0];
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            if (fa[i][j] < m)
                m = fa[i][j];
    return m;
}

int Raster::FloodCells(int t) const
{
    int c = 0;
    auto fa = FloodDepthGrid(t);
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            if (fa[i][j] > 0)
                c++;
    return c;
}

double Raster::FloodAvg(int t) const
{
    double s = 0;
    auto fa = FloodDepthGrid(t);
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            s += fa[i][j];
    return s / (rows * cols * 1.0);
}

double Raster::FloodVolume(int t) const
{
    double v = 0;
    auto fa = FloodDepthGrid(t);
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            v += fa[i][j];
    return v;
}

void Raster::exportFloodStat(const string &filename, int t) const
{
    static bool firstWrite = false;
    ofstream file(filename, ios::app);
    if (!file.is_open())
    {
        cout << "Error opening file\n";
        return;
    }
    if (!firstWrite)
    {
        file << "time,max,avg,cells,volume\n";
        firstWrite = true;
    }
    file << t << "," << FloodMax(t) << "," << FloodAvg(t) << ","
         << FloodCells(t) << "," << FloodVolume(t) << "\n";
    file.close();
}

vector<vector<double>> Raster::OutflowInflow(int t) const
{
    double k = 0.3;
    vector<vector<double>> flood(rows, vector<double>(cols, 0.0));
    auto fa = FloodDepthGrid(t);

    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
        {
            int currentDepth = fa[i][j];
            int bestdir = getFlowDirection(i, j);
            pair<int, int> p = nextCell(i, j, bestdir);

            int outflow = currentDepth * k;
            flood[i][j] += currentDepth - outflow;

            if (p.first < 0 || p.first >= rows ||
                p.second < 0 || p.second >= cols)
                continue;

            flood[p.first][p.second] += outflow;
        }
    }
    return flood;
}

static double greenAmptInfiltration(double Ks, double psi,
                                    double dTheta, double durationHr)
{
    if (Ks <= 0.0 || dTheta <= 0.0)
        return 0.0;

    double F = Ks * durationHr;
    for (int i = 0; i < 10; i++)
    {
        F = std::max(F, 1e-6);
        F = Ks * durationHr + psi * dTheta * std::log(1.0 + F / (psi * dTheta));
    }

    double rate = Ks * (1.0 + (psi * dTheta) / std::max(F, 1e-6));
    return rate;
}

static double manningVelocity(double n, double depth, double slope)
{
    depth = std::max(depth, 1e-6);
    slope = std::max(slope, 1e-6);
    n = std::max(n, 1e-6);
    return (1.0 / n) * std::pow(depth, 2.0 / 3.0) * std::sqrt(slope);
}

std::vector<std::vector<double>>
Raster::FloodDepthGridFinal(double rainfall,
                            double cellSize,
                            double manningN,
                            double durationHr,
                            double Ks,
                            double psi,
                            double dTheta) const
{
    auto fa = computeFlowAccumulation();

    double infiltration = greenAmptInfiltration(Ks, psi, dTheta, durationHr);
    double effectiveRain = std::max(rainfall - infiltration, 0.0);

    double intensityMs = effectiveRain / (1000.0 * 3600.0);

    std::vector<std::vector<double>> depth(rows, std::vector<double>(cols, 0.0));

    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
        {
            double area = fa[i][j] * cellSize * cellSize;
            double Q = 0.7 * intensityMs * area;

            double slope = std::max(computeSlopeAt(i, j, cellSize), 1e-4);

            double d = 0.1;
            for (int iter = 0; iter < 50; iter++)
            {
                double v = manningVelocity(manningN, d, slope);
                double newDepth = Q / (v * cellSize);
                newDepth = std::max(newDepth, 1e-9);
                d = 0.5 * d + 0.5 * newDepth; // damped update stops oscillation
                if (std::abs(newDepth - d) < 1e-7)
                    break;
            }
            depth[i][j] = d;
        }
    }

    return depth;
}

bool Raster::ValidCell() const { return true; }
double Raster::FloodPercentage() const { return 0.0; }