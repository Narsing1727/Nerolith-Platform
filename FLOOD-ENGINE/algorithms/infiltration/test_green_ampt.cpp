#include "green_ampt.h"
#include <iostream>
#include <cassert>
#include <cmath>

int main() {
    double Ks_sand  = 117.8, psi_sand  = 49.5,  dTheta_sand  = 0.417;
    double Ks_clay  = 0.3,   psi_clay  = 316.3,  dTheta_clay  = 0.385;
    double Ks_urban = 0.0,   psi_urban = 0.0,    dTheta_urban = 0.0;

    std::cout << "=== Test 1: Sand infiltrates faster than clay ===\n";
    double F_sand = cumulativeInfiltration(Ks_sand, psi_sand, dTheta_sand, 1.0);
    double F_clay = cumulativeInfiltration(Ks_clay, psi_clay, dTheta_clay, 1.0);
    std::cout << "Sand cumulative F(1hr): " << F_sand << " mm\n";
    std::cout << "Clay cumulative F(1hr): " << F_clay << " mm\n";
    assert(F_sand > F_clay);

    std::cout << "\n=== Test 2: Infiltration rate decreases over time ===\n";
    double f1 = infiltrationRate(Ks_sand, psi_sand, dTheta_sand, F_sand);
    double F2 = cumulativeInfiltration(Ks_sand, psi_sand, dTheta_sand, 6.0);
    double f2 = infiltrationRate(Ks_sand, psi_sand, dTheta_sand, F2);
    std::cout << "Rate at t=1hr: " << f1 << " mm/hr\n";
    std::cout << "Rate at t=6hr: " << f2 << " mm/hr\n";
    assert(f1 > f2);
    assert(f2 >= Ks_sand);

    std::cout << "\n=== Test 3: Rate approaches Ks at saturation ===\n";
    double F_large = cumulativeInfiltration(Ks_sand, psi_sand, dTheta_sand, 100.0);
    double f_sat   = infiltrationRate(Ks_sand, psi_sand, dTheta_sand, F_large);
    std::cout << "Rate at t=100hr (near saturated): " << f_sat << " mm/hr\n";
    std::cout << "Ks (sand): " << Ks_sand << " mm/hr\n";
    assert(f_sat < Ks_sand * 1.05);

    std::cout << "\n=== Test 4: Urban surface — zero infiltration ===\n";
    double F_urban = cumulativeInfiltration(Ks_urban, psi_urban, dTheta_urban, 1.0);
    std::cout << "Urban F(1hr): " << F_urban << " mm\n";
    assert(F_urban < 1e-3);

    std::cout << "\n=== Test 5: Fixed-point convergence check ===\n";
    double F_10  = cumulativeInfiltration(Ks_sand, psi_sand, dTheta_sand, 1.0, 10);
    double F_50  = cumulativeInfiltration(Ks_sand, psi_sand, dTheta_sand, 1.0, 50);
    std::cout << "F with 10 iterations: " << F_10 << "\n";
    std::cout << "F with 50 iterations: " << F_50 << "\n";
    assert(std::abs(F_10 - F_50) < 0.01);

    std::cout << "\nAll assertions passed.\n";
    return 0;
}
