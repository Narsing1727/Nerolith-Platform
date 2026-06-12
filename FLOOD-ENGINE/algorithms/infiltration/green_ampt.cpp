#include "green_ampt.h"
#include <cmath>
#include <algorithm>

double infiltrationRate(double Ks, double psi, double dTheta, double F) {
    F = std::max(F, 1e-6);
    return Ks * (1.0 + (psi * dTheta) / F);
}

double cumulativeInfiltration(double Ks, double psi, double dTheta, double t, int iterations) {
    if (Ks <= 0.0 || dTheta <= 0.0) return 0.0;

    double F = Ks * t;

    for (int i = 0; i < iterations; i++) {
        F = std::max(F, 1e-6);
        F = Ks * t + psi * dTheta * std::log(1.0 + F / (psi * dTheta));
    }

    return F;
}
